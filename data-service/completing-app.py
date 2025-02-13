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
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send

def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

def create_label_image(text, output_path):
    img = Image.new("RGB", (600, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
    except IOError:
        font_large = ImageFont.load_default()
    draw.text((10, 30), text, fill="black", font=font_large)
    img = img.resize((300, 125), Image.Resampling.LANCZOS)  # Oprava ANTIALIAS
    img.save(output_path)
    return output_path

def print_label(image_path, printer_path):
    ql = BrotherQLRaster("QL-1050")
    try:
        instructions = convert(ql, [image_path], label="62")  # Upravit podle štítku
        send(instructions, printer_identifier=printer_path, backend="linux_kernel", blocking=True)
        print("Label sent to printer.")
    except Exception as e:
        print(f"Printing error: {e}")

class PDFHandler(FileSystemEventHandler):
    def __init__(self, input_folder, archive_folder, config_path, output_dir, printer_path):
        self.input_folder = input_folder
        self.archive_folder = archive_folder
        self.config_path = config_path
        self.output_dir = output_dir
        self.printer_path = printer_path

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".pdf"):
            self.process_pdf(event.src_path)

    def process_pdf(self, pdf_path):
        try:
            config = load_config(self.config_path)
            text = extract_text_from_pdf(pdf_path)
            label_path = create_label_image(text[:30], os.path.join(self.output_dir, "label.png"))
            print_label(label_path, self.printer_path)
            shutil.move(pdf_path, os.path.join(self.archive_folder, os.path.basename(pdf_path)))
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

if __name__ == "__main__":
    input_folder = "./data/input"
    archive_folder = "./data/archiv"
    config_path = "config.yaml"
    output_dir = "./output-labels"
    printer_path = "/dev/usb/lp0"
    
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(archive_folder, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    event_handler = PDFHandler(input_folder, archive_folder, config_path, output_dir, printer_path)
    observer = Observer()
    observer.schedule(event_handler, input_folder, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
