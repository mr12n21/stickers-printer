import time
import os
import shutil
import re
import yaml
import pdfplumber
from PIL import Image, ImageDraw, ImageFont
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from brother_ql.raster import BrotherQLRaster  # type: ignore
from brother_ql.backends.helpers import send  # type: ignore
from brother_ql.conversion import convert  # type: ignore

# Function to load configuration
def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

# Check for blacklisted phrases in text
def contains_blacklisted_text(text, blacklist):
    return any(phrase in text for phrase in blacklist)

# Extract data from text
def extract_data_from_text(text, default_year):
    date_pattern = r"termín:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})"
    match = re.search(date_pattern, text)
    from_date = match.group(1) if match else "?"
    to_date = match.group(2) if match else "?"
    from_date_cleaned = ''.join(from_date.split())
    to_date_cleaned = ''.join(to_date.split())
    year = to_date_cleaned.split(".")[-1] if to_date_cleaned != "?" else str(default_year)
    var_symbol_pattern = r"Hotelový účet č.\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"
    return variable_symbol, from_date_cleaned, to_date_cleaned, year

# Find prefixes and associated data in text
def find_prefix_and_percentage(text, config):
    prefixes_found = {}
    karavan_found = False
    electric_found = False
    for rule in config.get("prefixes", []):
        pattern = rule.get("pattern")
        label = rule.get("label")
        if not pattern or not label:
            continue
        matches = re.findall(pattern, text)
        if matches:
            if label == "K":
                karavan_found = True
            elif label == "E":
                electric_found = True
            else:
                prefixes_found[label] = len(matches)
    return prefixes_found, karavan_found, electric_found

# Process the found prefixes and prepare the output string
def process_prefixes_and_output(prefixes_found, karavan_found):
    final_output = []
    if karavan_found:
        final_output.append("K")
    for prefix, count in prefixes_found.items():
        if count > 1:
            final_output.append(f"{count}{prefix}")
        else:
            final_output.append(prefix)
    final_output_string = "".join(final_output)
    return final_output_string

# Create a combined label image
def create_combined_label(variable_symbol, from_date, to_date, prefixes, year, output_path, final_output, electric_found):
    img = Image.new("RGB", (600, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font_year = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 240)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except IOError:
        font_large = font_medium = ImageFont.load_default()
    year_short = year[-2:]
    draw.text((280, 0), f"{year_short}", fill="#bfbfbf", font=font_year)
    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)
    to_date_formatted = ".".join(to_date.split(".")[:2]) + "."
    draw.text((10, 30), f"{to_date_formatted}", fill="black", font=font_large)
    if electric_found:
        draw.text((340, 30), "E", fill="black", font=font_large)
    draw.text((10, 120), final_output, fill="black", font=font_large)
    img.save(output_path)

# Function to print the label
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
        print(f"tisk '{image_path}' kompletni")
    except Exception as e:
        print(f"error: {e}")

# Watchdog handler for PDF processing and printing
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
            print(f"New PDF detected: {event.src_path}")
            self.process_pdf(event.src_path)

    def process_pdf(self, pdf_path):
        try:
            config = load_config(self.config_path)
            text = extract_text_from_pdf(pdf_path)
            blacklist = config.get("blacklist", [])
            if contains_blacklisted_text(text, blacklist):
                print(f"File {pdf_path} contains blacklisted text. Moving to archive.")
                shutil.move(pdf_path, os.path.join(self.archive_folder, os.path.basename(pdf_path)))
                return

            variable_symbol, from_date, to_date, year = extract_data_from_text(text, "2024")
            prefixes_found, karavan_found, electric_found = find_prefix_and_percentage(text, config)
            final_output = process_prefixes_and_output(prefixes_found, karavan_found)
            
            combined_file = os.path.join(self.output_dir, f"{variable_symbol.replace(' ', '_')}_combined_label.png")
            create_combined_label(variable_symbol, from_date, to_date, prefixes_found.keys(), year, combined_file, final_output, electric_found)
            print(f"Combined label created: {combined_file}")
            
            # Print the label after it's created
            print_label_with_image(combined_file, self.printer_model, self.usb_path)
            
            shutil.move(pdf_path, os.path.join(self.archive_folder, os.path.basename(pdf_path)))
            print(f"Moved {pdf_path} to archive.")

        except Exception as e:
            print(f"Error processing file {pdf_path}: {e}")

# Start the file watcher
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
    output_dir = "./output-labels"
    printer_model = 'QL-1050'
    usb_path = '/dev/usb/lp0'
    
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(archive_folder, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    start_watching(input_folder, archive_folder, config_path, output_dir, printer_model, usb_path)
