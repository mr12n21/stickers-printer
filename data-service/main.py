import pdfplumber  # type: ignore
import yaml
from PIL import Image, ImageDraw, ImageFont  # type: ignore
import os
import re

def load_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text

def find_prefix(text, rules):
    for rule in rules:
        if rule["match"].lower() in text.lower():
            return rule["prefix"]
    return "?"

def extract_data_from_text(text):
    date_pattern = r"term\u00edn:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4}),\s*host\u016f:\s*(\d+)"
    match = re.search(date_pattern, text)

    if match:
        from_date = match.group(1)  # Start date (e.g., 30. 12. 2024)
        to_date = match.group(2)  # End date (e.g., 1. 1. 2025)
        guests = match.group(3)  # Number of guests (e.g., 3)
    else:
        from_date = to_date = guests = "?"

    id_line = next((line for line in text.splitlines() if "Hotelov\u00fd ú\u010det" in line), "")
    invoice_id = "".join(filter(str.isdigit, id_line)) if id_line else "?"

    return invoice_id, from_date, to_date, guests

def create_label_png(invoice_id, from_date, to_date, guests, prefix, year, output_path):
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except IOError:
        font_large = font_medium = font_small = ImageFont.load_default()

    # Add year as background
    year_text = str(year)
    year_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 200)
    year_bbox = draw.textbbox((0, 0), year_text, font=year_font)
    year_width, year_height = year_bbox[2] - year_bbox[0], year_bbox[3] - year_bbox[1]
    draw.text(
        ((1150 - year_width) // 2, (400 - year_height) // 2),
        year_text,
        fill=(200, 200, 200),  # Light gray for background
        font=year_font,
        anchor="mm",
    )

    # Add other text on top
    draw.text((10, 10), f"VBS: {invoice_id}", fill="black", font=font_medium)

    prefix_with_guests = f"{prefix.upper()} {guests}"
    prefix_bbox = draw.textbbox((0, 0), prefix_with_guests, font=font_large)
    prefix_width, prefix_height = prefix_bbox[2] - prefix_bbox[0], prefix_bbox[3] - prefix_bbox[1]
    draw.text(((600 - prefix_width) // 2, (300 - prefix_height) // 3), prefix_with_guests, fill="black", font=font_large)

    # Save the final label
    img.save(output_path)

def process_pdfs(pdf_paths, config_path, output_dir):
    config = load_config(config_path)
    year = config.get("year", 2024)
    rules = config["rules"]

    os.makedirs(output_dir, exist_ok=True)

    for pdf_path in pdf_paths:
        text = extract_text_from_pdf(pdf_path)

        invoice_id, from_date, to_date, guests = extract_data_from_text(text)
        prefix = find_prefix(text, rules)

        output_file = os.path.join(output_dir, f"{invoice_id.replace(' ', '_')}_label.png")
        create_label_png(invoice_id, from_date, to_date, guests, prefix, year, output_file)

        print(f"Zpracov\u00e1n soubor {pdf_path}, v\u00fdstup: {output_file}")

if __name__ == "__main__":
    pdf_paths = [
        "./testing-data/testing2.pdf",
    ]
    config_path = "config.yaml"
    output_dir = "output-labels"

    process_pdfs(pdf_paths, config_path, output_dir)
