import shutil
import os

def move_to_archive(pdf_path, png_path):
    try:
        if not os.path.exists('./archive'):
            os.makedirs('./archive')

        shutil.move(pdf_path, os.path.join('./archive', os.path.basename(pdf_path)))
        shutil.move(png_path, os.path.join('./archive', os.path.basename(png_path)))
        print(f"Moved {pdf_path} and {png_path} to archive.")
    except Exception as e:
        print(f"Error moving files to archive: {e}")
