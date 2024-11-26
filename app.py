import schedule
import time
from service.xml_processor import process_xml_files
from service.pdf_generator import generate_pdf
from service.printer_service import print_pdf
from service.file_manager import manage_files

def run():
    schedule.every(5).seconds.do(process_xml_files)
    schedule.every(5).seconds.do(generate_pdf)
    schedule.every(5).seconds.do(print_pdf)
    schedule.every().day.at("00:00").do(manage_files)

    while True:
        schedule.run_pending()
        time.sleep(1)
        
if __name__ == "__main__":
    run()