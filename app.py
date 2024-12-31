import time
import threading
import importlib.util
import sys
import os

def import_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

pdf_service = import_module_from_file('pdf_service', './pdf-service.py')
file_service = import_module_from_file('file_service', './file-service.py')
png_service = import_module_from_file('png_service', './png-service.py')
printer_service = import_module_from_file('printer_service', './printer-service.py')

PDF_DIR = './pdf'
ARCHIVE_DIR = './archive'
OUTPUT_DIR = './output-labels'
CONFIG_PATH = 'config.yaml'
PRINTER_MODEL = 'QL-1050'
USB_PATH = '/dev/usb/lp0'

def monitor_pdf_folder():
    while True:
        for pdf_file in os.listdir(PDF_DIR):
            if pdf_file.endswith('.pdf'):
                pdf_path = os.path.join(PDF_DIR, pdf_file)
                print(f"Processing file: {pdf_path}")
                process_pdf(pdf_path)

        time.sleep(5)

def process_pdf(pdf_path):
    try:
        config = pdf_service.load_config(CONFIG_PATH)
        year = str(config.get("year", 2025))

        text = pdf_service.extract_text_from_pdf(pdf_path)
        variable_symbol, from_date, to_date, _ = pdf_service.extract_data_from_text(text, year)

        prefixes_found, karavan_found, electric_found = pdf_service.find_prefix_and_percentage(text, config)
        final_output = png_service.process_prefixes_and_output(prefixes_found, karavan_found)

        combined_file = os.path.join(OUTPUT_DIR, f"{variable_symbol.replace(' ', '_')}_combined_label.png")
        png_service.create_combined_label(variable_symbol, from_date, to_date, prefixes_found.keys(), year, combined_file, final_output, electric_found)

        printer_service.print_label_with_image(combined_file, PRINTER_MODEL, USB_PATH)

        file_service.move_to_archive(pdf_path, combined_file)

    except Exception as e:
        print(f"Error processing file {pdf_path}: {e}")

def start_monitoring():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    threading.Thread(target=monitor_pdf_folder, daemon=True).start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    start_monitoring()
