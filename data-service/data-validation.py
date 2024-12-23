import pdfplumber  # type: ignore
import yaml
from PIL import Image, ImageDraw, ImageFont  # type: ignore
import os
import re

def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text

def find_prefix(text, rules):
    for rule in rules:
        if rule["match"].lower() in text.lower():
            return rule["prefix"]
    return "?"

def extract_data_from_text(text):
    date_pattern = r"termín:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4}),\s*hostů:\s*(\d+)"
    match = re.search(date_pattern, text)
    from_date = match.group(1) if match else "?"
    to_date = match.group(2) if match else "?"
    guests = match.group(3) if match else "?"

    var_symbol_pattern = r"variabilní symbol:\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"

    return variable_symbol, from_date, to_date, guests

def create_label_png(variable_symbol, from_date, to_date, guests, prefix, year, output_path):
    img = Image.new("RGB", (600, 280), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 150)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except IOError:
        font_large = font_medium = font_small = ImageFont.load_default()
    
    year_text = str(year)
    year_bbox = draw.textbbox((0, 0), year_text, font=font_large)
    draw.text(((600 - year_bbox[2]) // 2, (280 - year_bbox[3]) // 2), year_text, fill=(200, 200, 200), font=font_large)

    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)
    prefix_with_guests = f"{prefix.upper()} {guests}"
    prefix_bbox = draw.textbbox((0, 0), prefix_with_guests, font=font_large)
    draw.text(((600 - prefix_bbox[2]) // 2, (280 - prefix_bbox[3]) // 3), prefix_with_guests, fill="black", font=font_large)
    draw.text((10, 240), f"Od: {from_date} Do: {to_date}", fill="black", font=font_small)
    
    img.save(output_path)

def process_pdfs(pdf_paths, config_path, output_dir):
    config = load_config(config_path)
    year = config.get("year", 2024)
    rules = config.get("rules", [])

    os.makedirs(output_dir, exist_ok=True)

    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"Error: File not found - {pdf_path}")
            continue
        try:
            text = extract_text_from_pdf(pdf_path)
            variable_symbol, from_date, to_date, guests = extract_data_from_text(text)
            prefix = find_prefix(text, rules)

            caravan_pattern = r"(Stání pro karavan|obytný přívěs|mikrobus|nákladní auto)"
            electricity_pattern = r"(Přípojka elektrického proudu)"
            caravan_match = re.search(caravan_pattern, text)
            electricity_match = re.search(electricity_pattern, text)

            if caravan_match:
                prefix = "K"
                to_date_short = re.search(r"-\s*(\d{1,2}\.\s*\d{1,2})", text).group(1) if re.search(r"-\s*(\d{1,2}\.\s*\d{1,2})", text) else "?"
            else:
                to_date_short = to_date
            if electricity_match:
                prefix += "E"

            output_file = os.path.join(output_dir, f"{variable_symbol.replace(' ', '_')}_label.png")
            create_label_png(variable_symbol, from_date, to_date_short, guests, prefix, year, output_file)
            print(f"Processed file {pdf_path}, output: {output_file}")
        except Exception as e:
            print(f"Error processing file {pdf_path}: {e}")

if __name__ == "__main__":
    pdf_paths = [
        "./testing-data/faktura_11.pdf",
    ]
    config_path = "config.yaml"
    output_dir = "output-labels"

    process_pdfs(pdf_paths, config_path, output_dir)
