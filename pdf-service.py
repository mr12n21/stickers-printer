import pdfplumber
import re

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

    from_date_cleaned = ''.join(from_date.split())
    to_date_cleaned = ''.join(to_date.split())

    year = to_date_cleaned.split(".")[-1] if to_date_cleaned != "?" else str(default_year)

    var_symbol_pattern = r"variabilní symbol:\s*(\d+)"
    var_symbol_match = re.search(var_symbol_pattern, text)
    variable_symbol = var_symbol_match.group(1) if var_symbol_match else "?"

    return variable_symbol, from_date_cleaned, to_date_cleaned, year

def find_prefix_and_percentage(text, config):
    prefixes_found = {}
    karavan_found = False
    electric_found = False

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
