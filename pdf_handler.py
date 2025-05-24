from pdf_processor import (
    extract_text_from_pdf,
    contains_blacklisted_text,
    extract_data_from_text,
    count_special_prefixes,
    find_prefix_and_percentage,
    process_prefixes_and_output
)
from label_generator import create_combined_label
from printer import print_label_with_image
from multiprocessing import Process

def process_pdf(pdf_file, config, printer_model, usb_path, test_mode=False):
    try:
        print("Zpracovávám PDF v paměti...")
        text = extract_text_from_pdf(pdf_file)

        blacklist = config.get("blacklist") or []
        if contains_blacklisted_text(text, blacklist):
            print("PDF obsahuje zakázaný text, přeskakuji zpracování.")
            return False

        default_year = config.get("year", 2024)
        variable_symbol, from_date, to_date, year = extract_data_from_text(text, default_year)

        special_counts = count_special_prefixes(text, config.get("special", []))
        standard_counts, electric_found = find_prefix_and_percentage(text, config)

        final_output, total_prints = process_prefixes_and_output(
            special_counts, standard_counts, electric_found
        )

        label_image = create_combined_label(
            variable_symbol, from_date, to_date, year, final_output, electric_found
        )

        if test_mode:
            print("\n[TEST MODE] Přeskočen reálný tisk. Simulace výstupu:")
            print(f"  - Proměnný symbol: {variable_symbol}")
            print(f"  - Období: {from_date} až {to_date}")
            print(f"  - Rok: {year}")
            print(f"  - Počet elektrických prefixů: {len(electric_found)}")
            print(f"  - Výstupní data pro štítky: {final_output}")
            print(f"  - Celkový počet štítků k tisku: {total_prints}")
        else:
            print("Spouštím tiskový proces...")
            print_process = Process(
                target=print_label_with_image,
                args=(label_image, printer_model, usb_path, total_prints)
            )
            print_process.start()

        return True

    except Exception as e:
        print(f"[CHYBA] Chyba při zpracování PDF: {e}")
        return False
