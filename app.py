import time
import threading
import os
from pdf_service import load_config, extract_text_from_pdf, extract_data_from_text, find_prefix_and_percentage
from png_service import process_prefixes_and_output, create_combined_label
from printer_service import print_label_with_image
from file_service import move_to_archive

#config
PDF_DIR = './pdf'
ARCHIVE_DIR = './archive'
OUTPUT_DIR = './output-labels'
CONFIG_PATH = 'config.yaml'
PRINTER_MODEL = 'QL-1050'
USB_PATH = '/dev/usb/lp0'

def process_pdf(pdf_path):
    try:
        config = load_config(CONFIG_PATH)
        year = str(config.get("year", 2025))

        text = extract_text_from_pdf(pdf_path)
        variable_symbol, from_date, to_date, _ = extract_data_from_text(text, year)

        prefixes_found, karavan_found, electric_found = find_prefix_and_percentage(text, config)
        final_output = process_prefixes_and_output(prefixes_found, karavan_found)

        combined_file = os.path.join(OUTPUT_DIR, f"{variable_symbol.replace(' ', '_')}_combined_label.png")
        create_combined_label(variable_symbol, from_date, to_date, prefixes_found.keys(), year, combined_file, final_output, electric_found)

        print_label_with_image(combined_file, PRINTER_MODEL, USB_PATH)

        move_to_archive(pdf_path, combined_file)

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

def monitor_pdf_folder():
    """
    Sleduje složku s PDF soubory a zpracovává je, jakmile jsou přidány.
    """
    while True:
        for pdf_file in os.listdir(PDF_DIR):
            if pdf_file.endswith('.pdf'):
                pdf_path = os.path.join(PDF_DIR, pdf_file)
                print(f"Processing: {pdf_path}")
                process_pdf(pdf_path)

        time.sleep(5)

def start_monitoring():
    """
    Spustí sledování složky s PDF soubory v samostatném vlákně.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    threading.Thread(target=monitor_pdf_folder, daemon=True).start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    start_monitoring()
