import pdfplumber  # type: ignore
import yaml  # type: ignore
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
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def extract_data_from_text(text, default_year):
    date_pattern = r"termín:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})"
    match = re.search(date_pattern, text)
    from_date = match.group(1) if match else "?"
    to_date = match.group(2) if match else "?"

    year = from_date.split(".")[-1] if from_date != "?" else str(default_year)

    var_symbol_pattern = r"variabilní symbol:\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"

    return variable_symbol, from_date, to_date, year

def find_prefix_and_percentage(text, config):
    prefixes_found = {}
    karavan_found = False
    electric_found = False  # Indikátor pro "E"

    for rule in config.get("prefixes", []):
        pattern = rule.get("pattern")
        label = rule.get("label")
        if not pattern or not label:
            continue

        matches = re.findall(pattern, text)

        if matches:
            if label == "K":
                karavan_found = True
            elif label == "E":
                electric_found = True
            else:
                prefixes_found[label] = len(matches)

    return prefixes_found, karavan_found, electric_found

def process_prefixes_and_output(prefixes_found, karavan_found):
    final_output = []

    if karavan_found:
        final_output.append("K")

    for prefix, count in prefixes_found.items():
        if count > 1:
            final_output.append(f"{count}{prefix}")
        else:
            final_output.append(prefix)

    final_output_string = "".join(final_output)
    print(f"Final output (bez E): {final_output_string}")
    return final_output_string

def create_combined_label(variable_symbol, from_date, to_date, prefixes, year, output_path, final_output, electric_found):
    img = Image.new("RGB", (600, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_year = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 240)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except IOError:
        font_large = font_medium = ImageFont.load_default()

    draw.text((280, 0), f"{year}", fill="#bfbfbf", font=font_year)

    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)
    to_date_formatted = f"{to_date.split('.')[0]}.{to_date.split('.')[1]}."
    draw.text((10, 30), f"{to_date_formatted}", fill="black", font=font_large)

    if electric_found:
        draw.text((350, 30), "E", fill="black", font=font_large)

    draw.text((10, 120), final_output, fill="black", font=font_large)

    img.save(output_path)

def process_pdfs(pdf_paths, config_path, output_dir):
    config = load_config(config_path)
    default_year = config.get("year", 2024)

    os.makedirs(output_dir, exist_ok=True)

    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"Error: File not found - {pdf_path}")
            continue
        try:
            text = extract_text_from_pdf(pdf_path)
            variable_symbol, from_date, to_date, year = extract_data_from_text(text, default_year)

            prefixes_found, karavan_found, electric_found = find_prefix_and_percentage(text, config)

            final_output = process_prefixes_and_output(prefixes_found, karavan_found)

            combined_file = os.path.join(output_dir, f"{variable_symbol.replace(' ', '_')}_combined_label.png")

            create_combined_label(variable_symbol, from_date, to_date, prefixes_found.keys(), year, combined_file, final_output, electric_found)
            print(f"Combined label created: {combined_file}")

        except Exception as e:
            print(f"Error processing file {pdf_path}: {e}")

if __name__ == "__main__":
    pdf_paths = [
        "./testing-data/faktura_11.pdf",
    ]
    config_path = "config.yaml"
    output_dir = "output-labels"

    process_pdfs(pdf_paths, config_path, output_dir)
