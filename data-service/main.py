import pdfplumber  # type: ignore
import yaml
from PIL import Image, ImageDraw, ImageFont  # type: ignore
import os

def load_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join(page.extract_text() for page in pdf.pages)
    return text

def find_prefix(text, rules):
    for rule in rules:
        if rule["match"].lower() in text.lower():
            return rule["prefix"]
    return "?"

def extract_data_from_text(text):
    id_line = next((line for line in text.splitlines() if "Hotelový účet" in line), "")
    invoice_id = id_line.split("č.")[1].strip() if "č." in id_line else "?"

    date_line = next((line for line in text.splitlines() if "termín:" in line), "")
    date_range = date_line.split("termín:")[1].strip() if "termín:" in date_line else "?"

    return invoice_id, date_range

def create_label_png(invoice_id, date_range, prefix, year, output_path):
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except IOError:
        font_large = ImageFont.load_default()

    font_small = ImageFont.load_default()
    draw.text((10, 10), prefix.upper(), fill="black", font=font_large)
    draw.text((10, 100), f"Datum: {date_range}", fill="black", font=font_small)
    img.save(output_path)

def process_pdfs(pdf_paths, config_path, output_dir):
    config = load_config(config_path)
    year = config.get("year", 2024)
    rules = config["rules"]

    os.makedirs(output_dir, exist_ok=True)

    for pdf_path in pdf_paths:
        text = extract_text_from_pdf(pdf_path)

        invoice_id, date_range = extract_data_from_text(text)
        prefix = find_prefix(text, rules)

        output_file = os.path.join(output_dir, f"{invoice_id.replace(' ', '_')}_label.png")
        create_label_png(invoice_id, date_range, prefix, year, output_file)

        print(f"Zpracován soubor {pdf_path}, výstup: {output-file}")

if __name__ == "__main__":
    pdf_paths = [
        "./testing-data/testing1.pdf",
    ]
    config_path = "config.yaml"
    output_dir = "output_labels"

    process_pdfs(pdf_paths, config_path, output_dir)
