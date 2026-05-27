# Projekt 3 – Elections Scraper

Implementace zadání ze souboru `3 (z wordu).pdf`. Skript stáhne výsledky
voleb do Poslanecké sněmovny 2017 z webu `volby.cz`, projde všechny obce
vybraného územního celku a uloží výsledky do `.csv`.

## Soubory

- `main.py` – kompletní scraper
- `requirements.txt` – seznam knihoven vygenerovaný z virtuálního prostředí
- `README.md` – dokumentace

> Pozn.: Vlastní aplikace zůstává v jediném souboru `main.py`, aby
> odpovídala omezení zadání.

## Instalace

```bash
cd /root/projekty/powerbi/3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Spuštění

Skript se spouští přes 2 argumenty:

1. URL územního celku (`ps32`)
2. název výstupního CSV souboru

```bash
python3 main.py \
  "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103" \
  vysledky_prostejov.csv
```

Pokud uživatel nezadá oba argumenty správně, program vypíše důvod a skončí.

## Co skript validuje

- že byly zadány přesně 2 argumenty,
- že URL směřuje na `volby.cz` a obsahuje `ps32`,
- že výstupní soubor končí na `.csv`.

Skript navíc umí rozpoznat i dočasnou nedostupnost `volby.cz` a místo
matoucí chyby z parsování skončí čitelnou hláškou.

## CSV výstup

Každý řádek odpovídá jedné obci a obsahuje:

- kód obce,
- název obce,
- voliči v seznamu,
- vydané obálky,
- platné hlasy,
- počty hlasů pro jednotlivé kandidující strany.

Pořadí stran ve sloupcích vychází z první úspěšně načtené obce a je následně
zachované pro všechny ostatní řádky.

## Struktura řešení

Kód je rozdělen do menších funkcí:

- `parse_args()` – ověří CLI argumenty,
- `fetch_soup()` – stáhne stránku a vrátí `BeautifulSoup`,
- `municipality_links()` – vybere odkazy na obce z okresní stránky,
- `parse_parties()` – načte hlasy pro kandidující strany,
- `parse_municipality()` – načte souhrnná data jedné obce,
- `write_csv()` – zapíše řádky do výstupního souboru,
- `scrape()` – propojí celý průchod scraperu,
- `main()` – CLI vstupní bod.

## Omezení zadání

- `requirements.txt` je generovaný seznam použitých knihoven,
- `3/main.py` má 166 řádků, takže splňuje limit max 200 řádků,
- scraper se nespouští při importu modulu, pouze při přímém spuštění.

## Ověření

Automatické testy pro tento projekt jsou v souboru
`tests/test_project_3_main.py`.

```bash
cd /root/projekty/powerbi
3/.venv/bin/pytest tests/test_project_3_main.py -q
```
