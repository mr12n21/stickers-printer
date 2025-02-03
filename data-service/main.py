import time
import os
import shutil
import re
import yaml
import pdfplumber
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

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

def contains_blacklisted_text(text, blacklist):
    for phrase in blacklist:
        if phrase in text:
            return True
    return False

class PDFHandler(FileSystemEventHandler):
    def __init__(self, input_folder, archive_folder, invalid_folder, config_path, output_dir):
        self.input_folder = input_folder
        self.archive_folder = archive_folder
        self.invalid_folder = invalid_folder
        self.config_path = config_path
        self.output_dir = output_dir

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
            
            if contains_blacklisted_text(text, config.get("blacklist", [])):
                print(f"File {pdf_path} contains blacklisted text. Moving to archive.")
                shutil.move(pdf_path, os.path.join(self.archive_folder, os.path.basename(pdf_path)))
                return
            
            print(f"File {pdf_path} does not match criteria. Moving to invalid folder.")
            shutil.move(pdf_path, os.path.join(self.invalid_folder, os.path.basename(pdf_path)))
            
        except Exception as e:
            print(f"Error processing file {pdf_path}: {e}")

def start_watching(input_folder, archive_folder, invalid_folder, config_path, output_dir):
    event_handler = PDFHandler(input_folder, archive_folder, invalid_folder, config_path, output_dir)
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
    archive_folder = "./data/archive"
    invalid_folder = "./data/invalid"
    config_path = "config.yaml"
    output_dir = "./output-labels"
    
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(archive_folder, exist_ok=True)
    os.makedirs(invalid_folder, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    start_watching(input_folder, archive_folder, invalid_folder, config_path, output_dir)