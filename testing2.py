import time
import os
import shutil
import re
import yaml
import pdfplumber
from PIL import Image, ImageDraw, ImageFont
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.conversion import convert

def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Konfigurační soubor nenalezen: {config_path}")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF soubor nenalezen: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def contains_blacklisted_text(text, blacklist):
    return any(phrase in text for phrase in blacklist)

def extract_data_from_text(text, default_year):
    date_pattern = r"termín:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})"
    match = re.search(date_pattern, text)
    from_date = match.group(1) if match else "?"
    to_date = match.group(2) if match else "?"
    from_date_cleaned = ''.join(from_date.split())
    to_date_cleaned = ''.join(to_date.split())

    var_symbol_pattern = r"Hotelový účet č.\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"
    return variable_symbol, from_date_cleaned, to_date_cleaned, default_year

def count_special_prefixes(text, special_config):
    special_counts = {}
    for rule in special_config:
        pattern = rule.get("pattern")
        label = rule.get("label")
        identifier = rule.get("identifier")
        if not pattern or not label or not identifier:
            continue
        
        p_pattern = rf"Ubytovací služby.*?(?:\b{identifier})(\d+|\w+)"
        p_matches = re.findall(p_pattern, text, re.DOTALL)
        unique_p_values = set(p_matches)
        count = len(unique_p_values)
        if count > 0:
            special_counts[label] = count
    
    return special_counts

def count_standard_prefixes(text, prefixes_config):
    prefixes_found = {}
    electric_found = False
    
    for rule in prefixes_config:
        pattern = rule.get("pattern")
        label = rule.get("label")
        if not pattern or not label:
            continue
        
        if label == "E":
            if re.search(pattern, text, re.DOTALL):
                electric_found = True
        else:
            matches = re.findall(rf"{pattern}.*?\|\s*(\d+)\s*\|", text, re.DOTALL)
            if matches:
                prefixes_found[label] = int(matches[-1])
    
    return prefixes_found, electric_found

def process_prefixes_and_output(special_counts, standard_counts, electric_found):
    final_output = []
    
    for label, count in special_counts.items():
        if count > 1:
            final_output.append(f"{count}{label}")
        else:
            final_output.append(label)
    
    for label, count in standard_counts.items():
        if count > 1:
            final_output.append(f"{count}{label}")
        else:
            final_output.append(label)
    
    if electric_found:
        final_output.append("E")
    
    return "".join(final_output)

def create_combined_label(variable_symbol, from_date, to_date, year, output_path, final_output, electric_found, config_year):
    img = Image.new("RGB", (600, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font_year = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 240)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except IOError:
        font_large = font_medium = ImageFont.load_default()
    
    year_short = str(config_year)[-2:]
    draw.text((280, 0), f"{year_short}", fill="#bfbfbf", font=font_year)
    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)
    to_date_formatted = ".".join(to_date.split(".")[:2]) + "."
    draw.text((10, 30), f"{to_date_formatted}", fill="black", font=font_large)
    if electric_found:
        draw.text((340, 30), "E", fill="black", font=font_large)
    draw.text((10, 120), final_output, fill="black", font=font_large)
    img.save(output_path)

"""
def print_label_with_image(image_path, printer_model, usb_path, label_type='62'):
    try:
        image = Image.open(image_path)
        image = image.convert('1')
        target_width = 696
        if image.width != target_width:
            scale_factor = target_width / image.width
            target_height = int(image.height * scale_factor)
            image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        qlr = BrotherQLRaster(printer_model)
        instructions = convert(qlr, [image], label=label_type, rotate='0')
        send(instructions, usb_path)
        print(f"Tisk '{image_path}' dokončen")
    except Exception as e:
        print(f"Chyba: {e}")
"""

class PDFHandler(FileSystemEventHandler):
    def __init__(self, input_folder, archive_folder, config_path, output_dir, printer_model, usb_path):
        self.input_folder = input_folder
        self.archive_folder = archive_folder
        self.config_path = config_path
        self.output_dir = output_dir
        self.printer_model = printer_model
        self.usb_path = usb_path

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".pdf"):
            print(f"Detekován nový PDF: {event.src_path}")
            self.process_pdf(event.src_path)

    def process_pdf(self, pdf_path):
        try:
            config = load_config(self.config_path)
            text = extract_text_from_pdf(pdf_path)
            blacklist = config.get("blacklist", [])
            if contains_blacklisted_text(text, blacklist):
                print(f"Soubor {pdf_path} obsahuje zakázaný text. Přesouvám do archivu.")
                shutil.move(pdf_path, os.path.join(self.archive_folder, os.path.basename(pdf_path)))
                return

            config_year = config.get("year", 2024)
            variable_symbol, from_date, to_date, year = extract_data_from_text(text, config_year)
            special_counts = count_special_prefixes(text, config.get("special", []))
            standard_counts, electric_found = count_standard_prefixes(text, config.get("prefixes", []))
            
            final_output = process_prefixes_and_output(special_counts, standard_counts, electric_found)
            total_prints = max(sum(special_counts.values()), 1)
            
            combined_file = os.path.join(self.output_dir, f"{variable_symbol.replace(' ', '_')}_combined_label.png")
            create_combined_label(variable_symbol, from_date, to_date, year, combined_file, final_output, electric_found, config_year)
            print(f"Vytvořen kombinovaný štítek: {combined_file}")
            
            for i in range(total_prints):
                print(f"Simulovaný tisk {i+1}/{total_prints} štítku: {combined_file}")
            
            shutil.move(pdf_path, os.path.join(self.archive_folder, os.path.basename(pdf_path)))
            print(f"Přesunut {pdf_path} do archivu.")

        except Exception as e:
            print(f"Chyba při zpracování souboru {pdf_path}: {e}")

def start_watching(input_folder, archive_folder, config_path, output_dir, printer_model, usb_path):
    event_handler = PDFHandler(input_folder, archive_folder, config_path, output_dir, printer_model, usb_path)
    observer = Observer()
    observer.schedule(event_handler, input_folder, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    input_folder = "./data/input"
    archive_folder = "./data/archiv"
    config_path = "config.yaml"
    output_dir = "./data/output-labels"
    printer_model = 'QL-1050'
    usb_path = '/dev/usb/lp0'
    
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(archive_folder, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    start_watching(input_folder, archive_folder, config_path, output_dir, printer_model, usb_path)