import re
import pdfplumber
import io

def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text if text else ""

def contains_blacklisted_text(text, blacklist):
    if text is None or blacklist is None:
        return False
    return any(phrase in text for phrase in blacklist)

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
            else:
                prefixes_found[label] = 1
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
    standard_output = []
    for label in standard_counts.keys():
        standard_output.append(label)
    standard_str = "".join(standard_output)
    electric_str = "E" if electric_found else ""
    final_output = special_str + standard_str + electric_str
    total_prints = 0
    for part in re.findall(r'(\d*[A-Za-z])', final_output):
        if part == "E":
            continue
        if part[:-1].isdigit():
            total_prints += int(part[:-1])
        else:
            total_prints += 1
    return final_output, total_prints