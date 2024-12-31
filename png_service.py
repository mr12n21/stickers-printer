from PIL import Image, ImageDraw, ImageFont
import os

def create_combined_label(variable_symbol, from_date, to_date, prefixes, year, output_path, final_output, electric_found):
    img = Image.new("RGB", (600, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_year = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 240)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except IOError:
        font_large = font_medium = ImageFont.load_default()

    year_short = year[-2:]
    draw.text((280, 0), f"{year_short}", fill="#bfbfbf", font=font_year)

    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)
    to_date_formatted = f"{to_date.split('.')[0]}.{to_date.split('.')[1]}."
    draw.text((10, 30), f"{to_date_formatted}", fill="black", font=font_large)

    if electric_found:
        draw.text((340, 30), "E", fill="black", font=font_large)

    draw.text((10, 120), final_output, fill="black", font=font_large)

    img.save(output_path)
