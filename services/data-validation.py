import yaml
import pdfplumber
from PIL import Image, ImageDraw, ImageFont

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
        match = rule.get("match")
        prefix = rule.get("prefix")
        if match in text:
            count = text.count(match)
            code += f"{prefix}{count}-"
    return code.rstrip("-")

def create_png_with_code(code, year, output_path):
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font = ImageFont.load_default()

    draw.text((10, 50), f"Kód: {code}", fill="black", font=font)

    rotated_year_img = Image.new("RGB", (20, 200), color=(255, 255, 255))
    rotated_draw = ImageDraw.Draw(rotated_year_img)
    rotated_draw.text((5, 80), str(year), fill="black", font=font)
    rotated_year_img = rotated_year_img.rotate(90, expand=1)

    img.paste(rotated_year_img, (350, 0))

    img.save(output_path)

if __name__ == "__main__":
    pdf_path = "data.pdf"
    config_path = "config.yaml"
    output_path = "output.png"

    config = load_config(config_path)

    year = config.get("year", 2024)

    text = extract_text_from_pdf(pdf_path)

    code = generate_code(text, config["rules"])

    create_png_with_code(code, year, output_path)

    print(f"Kód byl uložen do {output_path}")
