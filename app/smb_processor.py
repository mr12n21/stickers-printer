import os
import shutil
from .pdf_generator import generate_pdf
from .printer_service import print_label
from .rule_loader import load_rules, match_code

SMB_DIR = "./smb-share"
ARCHIVE_DIR = "./archive/pdfs"

rules = load_rules()

def extract_data_from_pdf(pdf_path):
    extracted_text = "2 people, 18 years old"
    return extracted_text

def process_smb_folder():
    if not os.path.exists(SMB_DIR):
        os.makedirs(SMB_DIR)

    for file_name in os.listdir(SMB_DIR):
        file_path = os.path.join(SMB_DIR, file_name)
        if file_name.endswith('.pdf'):
            data = extract_data_from_pdf(file_path)
            code = match_code(data, rules)
            generate_pdf(code)
            print_label(code)
            shutil.move(file_path, os.path.join(ARCHIVE_DIR, file_name))
