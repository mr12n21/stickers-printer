from reportlab.lib.pagesizes import A8 # type: ignore
from reportlab.pdfgen import canvas # type: ignore

OUTPUT_DIR = ""
PDF_DIR = ""
INPUT_FILE = ""

def generate_pdf():
    os.makedirs(PDF_DIR, exist_ok=True)
    input_path = os.path.join(OUTPUT_DIR, INPUT_FILE)
    if not os.path.exists(input_path):
        return

    with open(input_path, "r") as file:
        lines = file.readlines()

    for line in lines:
        code = line.strip()
        if not code:
            continue

        pdf_path = os.path.join(PDF_DIR, f"{code}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A7)
        c.setFont("Helvetica", 20)
        c.drawString(10, 50, f"Kód: {code}")
        c.save()
        print(f"Generated PDF: {pdf_path}")

    open(input_path, "w").close()