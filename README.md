# Stickers Printer pro Camp Sedmihorky

[![Camp Sedmihorky](https://img.shields.io/badge/Camp-Sedmihorky-blue)](https://campsedmihorky.cz)

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