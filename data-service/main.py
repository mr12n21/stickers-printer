import pdfplumber # type: ignore
import yaml
from PIL import Image, ImageDraw, ImageFont # type: ignore
import os

#nacteni souboru
def load_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

#extrakce dat
def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join(page.extract_text() for page in pdf.pages)
    return text

#hledani pomoci prefix
def find_prefix(text, rules):
    for rule in rules:
        if rule["match"].lower() in text.lower():
            return rule["prefix"]
    return "?"

def extract_data_from_text(text):
    #id faktury
    id_line = next((line for line in text.splitlines() if "Hotelový účet" in line), "")
    invoice_id = id_line.split("č.")[1].strip() if "č." in id_line else "?"

    #datum
    date_line = next((line for line in text.splitlines() if "termín:" in line), "")
    date_range = date_line.split("termín:")[1].strip() if "termín:" in date_line else "?"

    return invoice_id, date_range

#tvorba png stitku
def create_label_png(invoice_id, date_range, prefix, year, output_path):
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # fronta pro text
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

    #id faktury
    draw.text((10, 10), invoice_id, fill="black", font=font_small)

    #datum
    draw.text((10, 50), f"Datum: {date_range}", fill="black", font=font_small)

    #prefix
    draw.text((10, 90), f"Kód: {prefix}", fill="black", font=font_large)

    #otoceni roku
    rotated_year_img = Image.new("RGB", (20, 200), color=(255, 255, 255))
    rotated_draw = ImageDraw.Draw(rotated_year_img)
    rotated_draw.text((5, 80), str(year), fill="black", font=font_small)
    rotated_year_img = rotated_year_img.rotate(90, expand=1)
    img.paste(rotated_year_img, (370, 0))

    #ulozeni png
    img.save(output_path)

def process_pdfs(pdf_paths, config_path, output_dir):
    config = load_config(config_path)
    year = config.get("year", 2024)
    rules = config["rules"]

    os.makedirs(output_dir, exist_ok=True)

    for pdf_path in pdf_paths:
        text = extract_text_from_pdf(pdf_path)

        #extrahovani
        invoice_id, date_range = extract_data_from_text(text)
        prefix = find_prefix(text, rules)

        #make png
        output_file = os.path.join(output_dir, f"{invoice_id.replace(' ', '_')}_label.png")
        create_label_png(invoice_id, date_range, prefix, year, output_file)

        print(f"Zpracován soubor {pdf_path}, výstup: {output_file}")

if __name__ == "__main__":
    #cesa k pdf
    pdf_paths = [
        "/tesing-data/testing1.pdf",
    ]
    config_path = "config.yaml"
    output_dir = "output_labels"

    process_pdfs(pdf_paths, config_path, output_dir)
