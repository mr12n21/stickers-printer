import time
import os
import re
import pdfplumber
from PIL import Image, ImageDraw, ImageFont
import logging
from printer import print_label_with_image
import json
import shutil

logger = logging.getLogger(__name__)

def is_file_ready(file_path, timeout=10):
    logger.info(f"Checking if file is ready: {file_path}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open(file_path, 'rb') as f:
                f.read(1)
            logger.info(f"File {file_path} is ready.")
            return True
        except (IOError, PermissionError):
            logger.info(f"File {file_path} not ready, waiting...")
            time.sleep(1)
    logger.error(f"Timeout: File {file_path} not ready after {timeout} seconds.")
    return False

def extract_text_from_pdf(pdf_path):
    logger.info(f"Extracting text from: {pdf_path}")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        logger.info(f"Extracted text from {pdf_path}: {text[:100]}...")
    return text if text else ""

def contains_blacklisted_text(text, blacklist):
    if text is None or blacklist is None:
        return False
    result = any(phrase in text for phrase in blacklist)
    logger.info(f"Blacklist check: {result} (blacklist: {blacklist})")
    return result

def extract_data_from_text(text, default_year):
    if text is None:
        return "?", "?", "?", str(default_year)
    date_pattern = r"termín:\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\s*-\s*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})"
    match = re.search(date_pattern, text)
    from_date = match.group(1) if match else "?"
    to_date = match.group(2) if match else "?"
    from_date_cleaned = ''.join(from_date.split())
    to_date_cleaned = ''.join(to_date.split())
    year = to_date_cleaned.split(".")[-1] if to_date_cleaned != "?" else str(default_year)
    var_symbol_pattern = r"Hotelový účet č.\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"
    logger.info(f"Extracted data: var_symbol={variable_symbol}, from_date={from_date_cleaned}, to_date={to_date_cleaned}, year={year}")
    return variable_symbol, from_date_cleaned, to_date_cleaned, year

def count_special_prefixes(text, special_config):
    special_counts = {}
    if text is None or special_config is None:
        return special_counts
    for rule in special_config:
        pattern = rule.get("pattern")
        label = rule.get("label")
        identifier = rule.get("identifier")
        if not pattern or not label or not identifier:
            continue
        p_pattern = rf"Ubytovací služby.*?(?:\b{identifier})(\d+|\w+)"
        p_matches = re.findall(p_pattern, text, re.DOTALL)
        unique_p_values = set(p_matches)
        count = len(unique_p_values)
        if count > 0:
            special_counts[label] = count
        elif re.search(pattern, text, re.DOTALL):
            special_counts[label] = 1
        logger.info(f"Special prefix '{label}' - found: {special_counts.get(label, 0)}")
    return special_counts

def find_prefix_and_percentage(text, config):
    prefixes_found = {}
    electric_found = False
    if text is None or config is None:
        return prefixes_found, electric_found
    for rule in config.get("prefixes", []):
        pattern = rule.get("pattern")
        label = rule.get("label")
        if not pattern or not label:
            continue
        if re.search(pattern, text, re.DOTALL):
            if label == "E":
                electric_found = True
                logger.info("Detected electricity: E")
            else:
                prefixes_found[label] = 1
                logger.info(f"Detected prefix '{label}' (count ignored)")
        else:
            logger.info(f"Prefix '{label}' not found for pattern: {pattern}")
    return prefixes_found, electric_found

def process_prefixes_and_output(special_counts, standard_counts, electric_found):
    final_output = []
    special_output = []
    for label, count in special_counts.items():
        if count > 1:
            special_output.append(f"{count}{label}")
        else:
            special_output.append(label)
    special_str = "".join(special_output)
    if special_str:
        logger.info(f"Special prefixes: {special_str}")

    standard_output = []
    for label in standard_counts.keys():
        standard_output.append(label)
    standard_str = "".join(standard_output)
    if standard_str:
        logger.info(f"Standard prefixes: {standard_str}")

    electric_str = "E" if electric_found else ""
    if electric_found:
        logger.info("Detected electricity: E")

    final_output = special_str + standard_str + electric_str
    logger.info(f"Final prefix output: {final_output}")

    total_prints = 0
    for part in re.findall(r'(\d*[A-Za-z])', final_output):
        if part == "E":
            continue
        if part[:-1].isdigit():
            total_prints += int(part[:-1])
        else:
            total_prints += 1
    logger.info(f"Number of prints determined from '{final_output}': {total_prints}")

    return final_output, total_prints

def create_combined_label(variable_symbol, from_date, to_date, year, output_path, final_output, electric_found):
    logger.info(f"Creating label: {output_path}")
    img = Image.new("RGB", (600, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Inicializace výchozích fontů
    font_year = font_large = font_medium = ImageFont.load_default()
    try:
        font_year = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 240)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except IOError:
        logger.warning("Failed to load DejaVuSans-Bold font, using default font.")

    year_short = year[-2:]
    draw.text((280, 0), f"{year_short}", fill="#bfbfbf", font=font_year)
    draw.text((10, 10), f"ID: {variable_symbol}", fill="black", font=font_medium)
    to_date_formatted = ".".join(to_date.split(".")[:2]) + "."
    draw.text((10, 30), f"{to_date_formatted}", fill="black", font=font_large)
    if electric_found:
        draw.text((340, 30), "E", fill="black", font=font_large)
    draw.text((10, 120), final_output, fill="black", font=font_large)
    img.save(output_path)
    logger.info(f"Label saved: {output_path}")

def save_to_local(data, image_path, saved_labels_dir, test_mode):
    if not test_mode:
        logger.info("Not in test mode, skipping local save.")
        return

    os.makedirs(saved_labels_dir, exist_ok=True)
    timestamp = int(time.time())
    file_name = f"label_{data['variable_symbol']}_{timestamp}"

    # Uložit data jako JSON
    json_path = os.path.join(saved_labels_dir, f"{file_name}.json")
    with open(json_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info(f"Saved data to local: {json_path}")

    # Uložit PNG štítek
    if image_path and os.path.exists(image_path):
        png_path = os.path.join(saved_labels_dir, f"{file_name}.png")
        shutil.copy(image_path, png_path)
        logger.info(f"Saved image to local: {png_path}")

def process_pdf(pdf_path, config, output_dir, test_mode):
    try:
        logger.info(f"Processing PDF: {pdf_path}")
        if not is_file_ready(pdf_path):
            logger.error(f"File {pdf_path} not ready.")
            return None

        text = extract_text_from_pdf(pdf_path)
        blacklist = config.get("blacklist") or []
        if contains_blacklisted_text(text, blacklist):
            logger.info(f"File {pdf_path} contains blacklisted text.")
            return None

        default_year = config.get("year", 2025)
        variable_symbol, from_date, to_date, year = extract_data_from_text(text, default_year)
        special_counts = count_special_prefixes(text, config.get("special", []))
        standard_counts, electric_found = find_prefix_and_percentage(text, config)

        final_output, total_prints = process_prefixes_and_output(special_counts, standard_counts, electric_found)

        output_file = os.path.join(output_dir, f"label_{int(time.time())}.png" if test_mode else "label.png")
        create_combined_label(variable_symbol, from_date, to_date, year, output_file, final_output, electric_found)

        # Uložit data lokálně v testovacím režimu
        if test_mode:
            saved_labels_dir = config.get("saved_labels_dir", "/app/saved_labels")
            data_to_save = {
                "variable_symbol": variable_symbol,
                "from_date": from_date,
                "to_date": to_date,
                "year": year,
                "final_output": final_output,
                "electric_found": electric_found,
                "total_prints": total_prints
            }
            save_to_local(data_to_save, output_file, saved_labels_dir, test_mode)

        if total_prints > 0:
            print_label_with_image(output_file, test_mode, total_prints)

        return output_file

    except Exception as e:
        logger.error(f"Error processing file {pdf_path}: {e}")
        return None
