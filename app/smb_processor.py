import os
import shutil
from .pdf_generator import generate_pdf
from .printer_service import print_label

SMB_DIR = "./smb-share"
ARCHIVE_DIR = "./archive/pdfs"

def process_smb_folder():
    if not os.path.exists(SMB_DIR):
        os.makedirs(SMB_DIR)

    for file_name in os.listdir(SMB_DIR):
        file_path = os.path.join(SMB_DIR, file_name)
        if file_name.endswith('.pdf'):
            #generovani pdf
            code = extract_data_from_pdf(file_path)
            generate_pdf(code)
            #tisk
            print_label(code)
            #archivace
            shutil.move(file_path, os.path.join(ARCHIVE_DIR, file_name))
