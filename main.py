import os
import time
import re
import shutil
from datetime import datetime
import ntplib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import fitz
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

SMB_DIR = '/home/pi/smb_share/pdf_files'
ARCHIVE_DIR = '/home/pi/data-zaloha'

#nttp time for Prague
def get_current_time_ntp():
    client = ntplib.NTPClient()
    response = client.request('pool.ntp.org')
    utc_time = datetime.utcfromtimestamp(response.tx_time)
    prague_time = utc_time + timedelta(hours=2)
    return prague_time


#extract_data 
def extract_data_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text("text")
    doc.close()

    #find data
    elements = {}
    elements['Ubytovací služby'] = re.findall(r'Ubytovací služby.*?(\d{1,3} \d{3},\d{2} Kč)', text)
    elements['Poplatek z pobytu'] = re.findall(r'Poplatek z pobytu.*?(\d{1,3} \d{3},\d{2} Kč)', text)
    elements['Karavan'] = re.findall(r'(Karavan|Stan|Chatka)', text)
    elements['Počet osob'] = re.findall(r'(\d+)\s+osob', text)
    elements['Termín'] = re.findall(r'(\d{1,2}\.\d{1,2}\.\d{4})\s*-\s*(\d{1,2}\.\d{1,2}\.\d{4})', text)
    return elements

#def for make code for sticker
def create_label_code(elements, current_date):
    code = ""
    if "Karavan" in elements.get('Karavan', []):
        code += "K-"
    elif "Stan" in elements.get('Karavan', []):
        code += "S-"
    elif "Chatka" in elements.get('Karavan', []):
        code += "CH-"
    
    #pepole number
    number_of_people = elements.get('Počet osob', ['1'])[0]  # default to 1 person
    start_date, end_date = elements.get('Termín', ["01.01.2024", "01.01.2024"])
    code += f"Z-E-{number_of_people}-"
    code += f"{start_date}-{end_date}"
    return code

#make pdf for mini printer
def create_pdf_for_printer(label_code, current_date, output_path):
    c = canvas.Canvas(output_path, pagesize=(2 * inch, 5 * inch))
    c.drawString(10, 100, f"Label Code: {label_code}")
    #generation date for pdf
    formatted_date = current_date.strftime('%d.%m.%Y')
    c.drawString(10, 80, f"Date: {formatted_date}")

    c.save()

#move to zaloha
def move_to_archive(pdf_path):
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
    #time define
    timestamp = os.path.getctime(pdf_path)
    archived_pdf_path = os.path.join(ARCHIVE_DIR, f"{timestamp}_{os.path.basename(pdf_path)}")
    shutil.move(pdf_path, archived_pdf_path)
    print(f"Soubor {pdf_path} byl přesunut do archivu: {archived_pdf_path}")

#folder structure
class SMBEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.pdf'):
            print(f"Nový PDF soubor detekován: {event.src_path}")

            timestamp = os.path.getctime(event.src_path)
            elements = extract_data_from_pdf(event.src_path)
            current_date = get_current_time_ntp()
            label_code = create_label_code(elements, current_date)

            output_pdf_path = event.src_path.replace(".pdf", "_label.pdf")
            create_pdf_for_printer(label_code, current_date, output_pdf_path)
            print(f"Vytvořen štítek pro tisk: {output_pdf_path}")

            move_to_archive(event.src_path)

def main():
    event_handler = SMBEventHandler()
    observer = Observer()
    observer.schedule(event_handler, SMB_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
