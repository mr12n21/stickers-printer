import os
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def move_file(src_path, dest_path):
    try:
        if not os.path.exists(src_path):
            logging.error(f"Soubor {src_path} neexistuje.")
            return False
        shutil.move(src_path, dest_path)
        logging.info(f"Soubor {src_path} byl úspěšně přesunut do {dest_path}.")
        return True
    except Exception as e:
        logging.error(f"Chyba při přesouvání souboru {src_path}: {e}")
        return False

def create_dir_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Adresář {directory} byl vytvořen.")
    else:
        logging.info(f"Adresář {directory} již existuje.")

def clear_directory(directory):
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                logging.info(f"Soubor {filename} byl smazán.")
    except Exception as e:
        logging.error(f"Chyba při vymazávání souborů v {directory}: {e}")

def get_pdf_text(pdf_path):
    import pdfplumber
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except Exception as e:
        logging.error(f"Chyba při zpracování PDF souboru {pdf_path}: {e}")
    return text

def clean_text(text):
    return ''.join(e for e in text if e.isalnum() or e in ['.', '-', '_', ' '])
