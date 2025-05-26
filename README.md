# Stickers Printer pro Camp Sedmihorky

Tento projekt automatizuje zpracování "hotelových účtů" a nasledne generování štítků pro tisk
([campsedmihorky.cz](https://campsedmihorky.cz))

## Funkce
- Automatické sledování složky s PDF.
- Extrakce dat: variabilní symbol, datum, prefixy (např. "K" pro karavan, "E" pro elektřinu).
- Generování PNG štítků.
- Nalsedne tisknuti vystupu na tiskarnu.

## Požadavky
- Python 3.x
- Knihovny: `pdfplumber`, `PyYAML`, `Pillow`, `watchdog`, `brother_ql`
- Tiskárna Brother QL-1050

## Setup
- Vytvoření virtuálního prostředí: `python -m venv venv`
- Aktivace virtuálního prostředí: `source venv/bin/activate`
- Instalace knihoven: `pip install -r requirements.txt`
- Fonty: `sudo apt-get install fonts-dejavu/ sudo dnf install dejavu-sans-fonts`

## Run
- source venv/bin/activate
- python3 app.py
