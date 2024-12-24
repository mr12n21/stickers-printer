import pdfplumber  # type: ignore
import yaml
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
    """Extract text from a PDF file."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text

def extract_data_from_text(text):
    """Extract necessary data (variable symbol, dates, guests) from extracted PDF text."""
    date_pattern = r"termín:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4}),\s*hostů:\s*(\d+)"
    match = re.search(date_pattern, text)
    from_date = match.group(1) if match else "?"
    to_date = match.group(2) if match else "?"
    guests = match.group(3) if match else "?"

    year = from_date.split(".")[-1]

    var_symbol_pattern = r"variabilní symbol:\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"

    return variable_symbol, from_date, to_date, guests, year

def create_combined_label(variable_symbol, from_date, to_date, guests, prefix, year, output_path, background_color):
    """Create a label image with text drawn on it."""
    img = Image.new("RGB", (600, 200), color=background_color)
    draw = ImageDraw.Draw(img)
    
    try:
        font_year = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 200)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except IOError:
        font_large = font_medium = font_small = ImageFont.load_default()

    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)

    prefix_with_guests = f"{prefix.upper()} {guests}"

    to_date_without_year = to_date.split(".")[0] + "." + to_date.split(".")[1]
    draw.text((10, 50), f"K: {to_date_without_year}", fill="black", font=font_large)

    draw.text((320, 50), "E:", fill="black", font=font_large)

    year_text = f"Year: {year}"
    
    year_text_bbox = draw.textbbox((0, 0), year_text, font=font_large)
    year_text_width = year_text_bbox[2] - year_text_bbox[0]
    year_text_height = year_text_bbox[3] - year_text_bbox[1]
    
    year_box_x = 10
    year_box_y = 120
    year_box_width = year_text_width + 20
    year_box_height = year_text_height + 10

    draw.rectangle([year_box_x, year_box_y, year_box_x + year_box_width, year_box_y + year_box_height], fill="#b0b0b0")

    draw.text((year_box_x + 10, year_box_y + 5), year_text, fill="black", font=font_small)

    draw.text((10, 150), "Další služby:", fill="black", font=font_medium)

    img.save(output_path)

def process_pdfs(pdf_paths, config_path, output_dir):
    """Process PDF files, extract data, and create labels."""
    config = load_config(config_path)
    year = config.get("year", 2024)
    background_color = config.get("background_color", "#e0e0e0")
    rules = config.get("rules", [])

    os.makedirs(output_dir, exist_ok=True)

    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"Error: File not found - {pdf_path}")
            continue
        try:
            text = extract_text_from_pdf(pdf_path)
            variable_symbol, from_date, to_date, guests, year = extract_data_from_text(text)

            caravan_pattern = r"(Stání pro karavan|obytný přívěs|mikrobus|nákladní auto)"
            electricity_pattern = r"(Přípojka elektrického proudu)"
            caravan_match = re.search(caravan_pattern, text)
            electricity_match = re.search(electricity_pattern, text)

            if caravan_match or electricity_match:
                prefix = "K" if caravan_match else "E"
                combined_file = os.path.join(output_dir, f"{variable_symbol.replace(' ', '_')}_combined_label.png")
                create_combined_label(variable_symbol, from_date, to_date, guests, prefix, year, combined_file, background_color)
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
