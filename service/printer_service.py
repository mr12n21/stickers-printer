import os
import cups

PDF_DIR = "./archive/pdfs"

def print_pdf():
    """Odesílá PDF dokumenty na tiskárnu."""
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_name = next(iter(printers.keys()), None)

    if not printer_name:
        print("No printers found.")
        return

    for file_name in os.listdir(PDF_DIR):
        if file_name.endswith(".pdf"):
            file_path = os.path.join(PDF_DIR, file_name)
            try:
                conn.printFile(printer_name, file_path, "PDF Print", {})
                print(f"Sent to printer: {file_name}")
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to print {file_name}: {e}")
