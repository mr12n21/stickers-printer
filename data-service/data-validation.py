import pdfplumber  # type: ignore
import yaml  # type: ignore
from PIL import Image, ImageDraw, ImageFont  # type: ignore
import os
import re


def load_config(config_path):
    """Load configuration from a YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def extract_text_from_pdf(pdf_path):
    """Extract text from all pages in a PDF file."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text


def extract_data_from_text(text, year):
    """Extract necessary data (variable symbol, dates) from extracted PDF text."""
    date_pattern = r"termín:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})"
    match = re.search(date_pattern, text)
    from_date = match.group(1) if match else "?"
    to_date = match.group(2) if match else "?"

    year = from_date.split(".")[-1][-2:] if from_date != "?" else year

    var_symbol_pattern = r"variabilní symbol:\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"

    return variable_symbol, from_date, to_date, year


def determine_prefixes(text, config):
    """Determine all prefixes from the configuration."""
    prefixes = []
    for rule in config.get("prefixes", []):
        pattern = rule.get("pattern")
        label = rule.get("label")
        if not pattern or not label:
            continue
        print(f"Testing pattern: {pattern}")
        match = re.search(pattern, text)
        if match:
            print(f"Match found for label {label} with pattern {pattern}")
            prefixes.append(label)
    return prefixes


def create_combined_label(variable_symbol, from_date, to_date, prefixes, year, output_path):
    """Create a label image with text drawn on it."""
    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_year = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 210)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 85)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except IOError:
        font_large = font_medium = ImageFont.load_default()

    draw.text((280, 0), f"{year}", fill="#bfbfbf", font=font_year)

    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)

    to_date_formatted = f"{to_date.split('.')[0]}.{to_date.split('.')[1]}."
    draw.text((10, 50), f"{to_date_formatted}", fill="black", font=font_large)

    prefix_line = " ".join(prefixes)
    draw.text((10, 240), prefix_line, fill="black", font=font_medium)

    img.save(output_path)


def process_pdfs(pdf_paths, config_path, output_dir):
    """Process a list of PDF files and generate labels based on configuration."""
    config = load_config(config_path)
    year = config.get("year", 2024)

    os.makedirs(output_dir, exist_ok=True)

    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"Error: File not found - {pdf_path}")
            continue
        try:
            text = extract_text_from_pdf(pdf_path)
            print("Extracted text from PDF:\n", text)

            variable_symbol, from_date, to_date, year = extract_data_from_text(text, year)

            prefixes = determine_prefixes(text, config)

            print(f"Prefixes found: {prefixes}")

            combined_file = os.path.join(output_dir, f"{variable_symbol.replace(' ', '_')}_combined_label.png")
            create_combined_label(variable_symbol, from_date, to_date, prefixes, year, combined_file)
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
