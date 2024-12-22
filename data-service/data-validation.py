import pdfplumber
import yaml
from PIL import Image, ImageDraw, ImageFont
import os

def load_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join(page.extract_text() for page in pdf.pages)
    return text

def generate_code(text, rules):
    code = ""
    for rule in rules:
        match = rule.get("match").lower()
        prefix = rule.get("prefix")
        if match in text.lower():
            count = text.lower().count(match)
            code += f"{prefix}{count}-" if count > 1 else f"{prefix}-"
    return code.rstrip("-")

def create_png_with_code(code, year, host_name, output_path):
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font = ImageFont.load_default()

    draw.text((10, 10), f"Host: {host_name}", fill="black", font=font)

    draw.text((10, 50), f"Kód: {code}", fill="black", font=font)

    rotated_year_img = Image.new("RGB", (30, 300), color=(255, 255, 255))
    rotated_draw = ImageDraw.Draw(rotated_year_img)
    rotated_draw.text((5, 120), str(year), fill="black", font=font)
    rotated_year_img = rotated_year_img.rotate(90, expand=1)

    img.paste(rotated_year_img, (550, 0))

    img.save(output_path)

def process_pdfs(pdf_paths, config_path, output_dir):
    config = load_config(config_path)
    year = config.get("year", 2024)
    rules = config["rules"]

    os.makedirs(output_dir, exist_ok=True)

    for pdf_path in pdf_paths:
        text = extract_text_from_pdf(pdf_path)

        host_name_line = [line for line in text.split("\n") if "Hotelový účet" in line]
        host_name = host_name_line[0].split("-")[-1].strip() if host_name_line else "Neznámý host"

        code = generate_code(text, rules)

        output_file = os.path.join(output_dir, f"{host_name}_code.png")
        create_png_with_code(code, year, host_name, output_file)

        print(f"Zpracován soubor {pdf_path}, výstup: {output_file}")

if __name__ == "__main__":
    pdf_paths = [
        "./testing-data/testing1.pdf",
    ]
    config_path = "config.yaml"
    output_dir = "output_pngs"

    process_pdfs(pdf_paths, config_path, output_dir)
