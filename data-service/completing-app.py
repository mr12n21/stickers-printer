import time
import os
import shutil
import re
import yaml
import logging
import pdfplumber
from PIL import Image, ImageDraw, ImageFont
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send

# Nastavení logování
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Konfigurace cest
INPUT_FOLDER = "./data/input"
ARCHIVE_FOLDER = "./data/archive"
CONFIG_PATH = "config.yaml"
OUTPUT_FOLDER = "./output-labels"
LABEL_IMAGE = "/tmp/label.png"

# Nastavení tiskárny
PRINTER_MODEL = "QL-1050"
PRINTER_INTERFACE = "/dev/usb/lp0"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages)
    return text

def extract_data_from_text(text, default_year):
    date_pattern = r"termín:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})"
    match = re.search(date_pattern, text)
    from_date = match.group(1) if match else "?"
    to_date = match.group(2) if match else "?"
    var_symbol_pattern = r"Hotelový účet č.\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"
    return variable_symbol, from_date, to_date, default_year

def create_label_image(variable_symbol, from_date, to_date, year):
    img = Image.new("RGB", (600, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except IOError:
        font_large = font_medium = ImageFont.load_default()
    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)
    draw.text((10, 50), f"{to_date}", fill="black", font=font_large)
    img.save(LABEL_IMAGE)

def print_label():
    ql = BrotherQLRaster(PRINTER_MODEL)
    img = Image.open(LABEL_IMAGE)
    instructions = convert(ql, [img], label="62", rotate="0")
    send(instructions, PRINTER_INTERFACE)
    logging.info("Štítek byl úspěšně vytištěn.")

class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".pdf"):
            return
        logging.info(f"Nový PDF soubor detekován: {event.src_path}")
        process_pdf(event.src_path)

def process_pdf(pdf_path):
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            logging.warning("Žádný text v PDF, soubor přeskočen.")
            return
        variable_symbol, from_date, to_date, year = extract_data_from_text(text, "2024")
        create_label_image(variable_symbol, from_date, to_date, year)
        print_label()
        shutil.move(pdf_path, os.path.join(ARCHIVE_FOLDER, os.path.basename(pdf_path)))
        logging.info(f"Soubor {pdf_path} archivován.")
    except Exception as e:
        logging.error(f"Chyba při zpracování PDF: {e}")

def start_watching():
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    event_handler = PDFHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_FOLDER, recursive=False)
    observer.start()
    logging.info("Sledování složky spuštěno...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":import time
import os
import shutil
import re
import yaml
import logging
import pdfplumber
from PIL import Image, ImageDraw, ImageFont
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

INPUT_FOLDER = "./data/input"
ARCHIVE_FOLDER = "./data/archive"
CONFIG_PATH = "config.yaml"
OUTPUT_FOLDER = "./output-labels"
LABEL_IMAGE = "/tmp/label.png"

PRINTER_MODEL = "QL-1050"
PRINTER_INTERFACE = "/dev/usb/lp0"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages)
    return text

def extract_data_from_text(text, default_year):
    date_pattern = r"termín:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})"
    match = re.search(date_pattern, text)
    from_date = match.group(1) if match else "?"
    to_date = match.group(2) if match else "?"
    var_symbol_pattern = r"Hotelový účet č.\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"
    return variable_symbol, from_date, to_date, default_year

def create_label_image(variable_symbol, from_date, to_date, year):
    img = Image.new("RGB", (600, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except IOError:
        font_large = font_medium = ImageFont.load_default()
    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)
    draw.text((10, 50), f"{to_date}", fill="black", font=font_large)
    img.save(LABEL_IMAGE)

def print_label():
    ql = BrotherQLRaster(PRINTER_MODEL)
    img = Image.open(LABEL_IMAGE)
    instructions = convert(ql, [img], label="62", rotate="0")
    send(instructions, PRINTER_INTERFACE)
    logging.info("Štítek byl úspěšně vytištěn.")

class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".pdf"):
            return
        logging.info(f"Nový PDF soubor detekován: {event.src_path}")
        process_pdf(event.src_path)

def process_pdf(pdf_path):
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            logging.warning("Žádný text v PDF, soubor přeskočen.")
            return
        variable_symbol, from_date, to_date, year = extract_data_from_text(text, "2024")
        create_label_image(variable_symbol, from_date, to_date, year)
        print_label()
        shutil.move(pdf_path, os.path.join(ARCHIVE_FOLDER, os.path.basename(pdf_path)))
        logging.info(f"Soubor {pdf_path} archivován.")
    except Exception as e:
        logging.error(f"Chyba při zpracování PDF: {e}")

def start_watching():
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    event_handler = PDFHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_FOLDER, recursive=False)
    observer.start()
    logging.info("Sledování složky spuštěno...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watching()

    start_watching()
