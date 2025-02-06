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

#config
INPUT_FOLDER = "./data/input"
ARCHIVE_FOLDER = "./data/archiv"
OUTPUT_DIR = "./output-labels"
PRINTED_DIR = "./printed-labels"
CONFIG_PATH = "config.yaml"
PRINTER_MODEL = 'QL-1050'
USB_PATH = '/dev/usb/lp0'
LABEL_TYPE = '62'

#function
def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        text = "".join([page.extract_text() or "" for page in pdf.pages])
    return text

def contains_blacklisted_text(text, blacklist):
    return any(phrase in text for phrase in blacklist)

def extract_data_from_text(text, default_year):
    date_pattern = r"termín:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})"
    match = re.search(date_pattern, text)
    from_date, to_date = (match.group(1) if match else "?"), (match.group(2) if match else "?")

    year = to_date.split(".")[-1] if to_date != "?" else str(default_year)

    var_symbol_pattern = r"Hotelový účet č.\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"

    return variable_symbol, from_date.replace(" ", ""), to_date.replace(" ", ""), year

def find_prefix_and_percentage(text, config):
    prefixes_found, karavan_found, electric_found = {}, False, False
    for rule in config.get("prefixes", []):
        pattern, label = rule.get("pattern"), rule.get("label")
        if pattern and label:
            matches = re.findall(pattern, text)
            if matches:
                if label == "K":
                    karavan_found = True
                elif label == "E":
                    electric_found = True
                else:
                    prefixes_found[label] = len(matches)
    return prefixes_found, karavan_found, electric_found

def process_prefixes_and_output(prefixes_found, karavan_found):
    final_output = ["K"] if karavan_found else []
    for prefix, count in prefixes_found.items():
        final_output.append(f"{count}{prefix}" if count > 1 else prefix)
    return "".join(final_output)

def create_combined_label(variable_symbol, from_date, to_date, year, output_path, final_output, electric_found):
    img = Image.new("RGB", (600, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font_year = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 200)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except IOError:
        font_large = font_medium = ImageFont.load_default()

    year_short = year[-2:]

    #config text for year
    draw.text((280, 20), f"{year_short}", fill="#bfbfbf", font=font_year)
    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)
    draw.text((10, 30), f"{to_date}", fill="black", font=font_large)
    if electric_found:
        draw.text((340, 30), "E", fill="black", font=font_large)
    draw.text((10, 120), final_output, fill="black", font=font_large)

    img.save(output_path)

def print_label_with_image(image_path):
    try:
        image = Image.open(image_path).convert('1')
        image = image.resize((696, int(image.height * (696 / image.width))), Image.Resampling.LANCZOS)
        qlr = BrotherQLRaster(PRINTER_MODEL)
        instructions = convert(qlr, [image], label=LABEL_TYPE, rotate='0')
        send(instructions, USB_PATH)
        print(f"Tisk '{image_path}' dokončen")
    except Exception as e:
        print(f"Chyba při tisku: {e}")

#directory service
class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".pdf"):
            return
        print(f"Nový PDF soubor: {event.src_path}")
        self.process_pdf(event.src_path)

    def process_pdf(self, pdf_path):
        try:
            config = load_config(CONFIG_PATH)
            text = extract_text_from_pdf(pdf_path)
            if contains_blacklisted_text(text, config.get("blacklist", [])):
                shutil.move(pdf_path, os.path.join(ARCHIVE_FOLDER, os.path.basename(pdf_path)))
                return

            var_symbol, from_date, to_date, year = extract_data_from_text(text, "2024")
            prefixes_found, karavan_found, electric_found = find_prefix_and_percentage(text, config)
            final_output = process_prefixes_and_output(prefixes_found, karavan_found)

            output_file = os.path.join(OUTPUT_DIR, f"{var_symbol}_label.png")
            create_combined_label(var_symbol, from_date, to_date, year, output_file, final_output, electric_found)
            print(f"Vytvořen štítek: {output_file}")

            shutil.move(pdf_path, os.path.join(ARCHIVE_FOLDER, os.path.basename(pdf_path)))
            print(f"Soubor {pdf_path} přesunut do archivu.")

            print_label_with_image(output_file)
            shutil.move(output_file, os.path.join(PRINTED_DIR, os.path.basename(output_file)))

        except Exception as e:
            print(f"Chyba při zpracování {pdf_path}: {e}")

def start_watching():
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PRINTED_DIR, exist_ok=True)

    observer = Observer()
    observer.schedule(PDFHandler(), INPUT_FOLDER, recursive=False)
    observer.start()
    print("Systém sleduje složku pro nové PDF soubory...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watching()
