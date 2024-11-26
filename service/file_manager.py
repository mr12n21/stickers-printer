import os
import shutil
import time

SMB_DIR = ""
ARCHIVE_DIR = ""
MONTHLY_CLEAR = 30 * 24 * 60 * 60

def manage_files():
    for file_name in os.listdir(SMB_DIR):
        file_path = os.path.join(SMB_DIR, file_name)
        if os.path.isfile(file_path):
            shutil.move(file_path, ARCHIVE_DIR)
            
    current_time = time.time()
    for file_name in os.listdir(ARCHIVE_DIR):
        file_path = os.path.join(ARCHIVE_DIR, file_name)
        if os.path.isfile(file_path):
            file_time = os.path.getmtime(file_path)
            if current_time - file_time > MONTHLY_CLEAR:
                os.remove(file_path)
                print(f"Deleted old file: {file_name}")
