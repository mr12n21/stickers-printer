from reportlab.pdfgen import canvas
import os

PDF_DIR = "./archive/printed"

def generate_pdf(code):
    os.makedirs(PDF_DIR, exist_ok=True)
    pdf_path = os.path.join(PDF_DIR, f"{code}.pdf")
    #rozmer pro stitek
    c = canvas.Canvas(pdf_path, pagesize=(165, 165))
    c.setFont("Helvetica", 20)
    c.drawString(10, 80, f"Kód: {code}")
    c.save()
    return pdf_path

def extract_data_from_pdf(pdf_path):
    #simulace
    return "o(2)"
