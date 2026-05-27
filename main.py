import csv
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.volby.cz/pls/ps2017nss/"
HEADERS = {"User-Agent": "Mozilla/5.0 (ElectionsScraper/1.0)"}
OUTAGE_MARKER = "dočasnou nedostupnost internetové prezentace výsledků voleb"


def decode_response(response: requests.Response) -> str:
    """Decode HTML using a practical encoding for volby.cz pages."""
    encoding = response.encoding
    if not encoding or encoding.lower() == "iso-8859-1":
        encoding = response.apparent_encoding or "utf-8"
    return response.content.decode(encoding, errors="replace")


def fetch_soup(url: str) -> BeautifulSoup:
    """Download page and return parsed HTML soup."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(f"Failed to download page: {exc}") from exc
    text = decode_response(response)
    if OUTAGE_MARKER in text:
        raise SystemExit("Volby.cz is temporarily unavailable. Try again later.")
    return BeautifulSoup(text, "html.parser")


def parse_args(argv: list[str]) -> tuple[str, str]:
    """Parse and validate CLI arguments."""
    if len(argv) != 3:
        raise SystemExit(
            "Usage: python3 main.py <district_url_ps32> <output.csv>"
        )
    url, output = argv[1], argv[2]
    if "ps32" not in url or "volby.cz" not in url:
        raise SystemExit("Invalid URL. Use a district link from volby.cz (ps32).")
    if not output.lower().endswith(".csv"):
        raise SystemExit("Output file must have .csv extension.")
    return url, output


def clean_int(text: str) -> int:
    """Convert Czech-formatted integer text to int."""
    return int(text.replace("\xa0", "").replace(" ", ""))


def municipality_links(district_soup: BeautifulSoup, district_url: str) -> list[tuple[str, str, str]]:
    """Return list of (code, name, municipality_result_url)."""
    rows = district_soup.find_all("tr")
    items: list[tuple[str, str, str]] = []

    for row in rows:
        code_cell = row.find("td", class_="cislo")
        name_cell = row.find("td", class_="overflow_name")
        if not code_cell or not name_cell:
            continue

        code = code_cell.get_text(strip=True)
        name = name_cell.get_text(strip=True)
        link = code_cell.find("a") or name_cell.find("a")
        if not link or not link.get("href"):
            continue

        href = link["href"]
        if "ps311" not in href:
            continue
        items.append((code, name, urljoin(district_url, href)))

    if not items:
        raise SystemExit("No municipality links found. Check the input URL.")
    return items


def parse_parties(muni_soup: BeautifulSoup) -> dict[str, int]:
    """Parse party names and vote counts from municipality page."""
    names = [n.get_text(strip=True) for n in muni_soup.find_all("td", class_="overflow_name")]
    votes = []
    for cell in muni_soup.find_all("td"):
        header = cell.get("headers", [])
        header_values = header if isinstance(header, list) else [header]
        if any(value.startswith("t1sb3") or value.startswith("t2sb3") for value in header_values):
            votes.append(clean_int(cell.get_text(strip=True)))

    party_votes = dict(zip(names, votes))
    if not party_votes:
        raise SystemExit("Failed to parse party votes from municipality page.")
    return party_votes


def parse_municipality(url: str) -> tuple[int, int, int, dict[str, int]]:
    """Parse municipality totals and votes per party."""
    soup = fetch_soup(url)

    voters = soup.find("td", headers="sa2")
    envelopes = soup.find("td", headers="sa3")
    valid = soup.find("td", headers="sa6")
    if not voters or not envelopes or not valid:
        raise SystemExit("Failed to parse totals (voters/envelopes/valid votes).")

    party_votes = parse_parties(soup)
    return (
        clean_int(voters.get_text(strip=True)),
        clean_int(envelopes.get_text(strip=True)),
        clean_int(valid.get_text(strip=True)),
        party_votes,
    )


def write_csv(path: str, rows: list[dict[str, int | str]], party_columns: list[str]) -> None:
    """Write scraped data to CSV file."""
    base_columns = [
        "kód obce",
        "název obce",
        "voliči v seznamu",
        "vydané obálky",
        "platné hlasy",
    ]
    fieldnames = base_columns + party_columns

    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def scrape(district_url: str, output_file: str) -> None:
    """Run complete scraping flow for district URL."""
    district_soup = fetch_soup(district_url)
    municipalities = municipality_links(district_soup, district_url)

    rows: list[dict[str, int | str]] = []
    party_order: list[str] = []

    for code, name, url in municipalities:
        voters, envelopes, valid, party_votes = parse_municipality(url)

        if not party_order:
            party_order = list(party_votes.keys())

        row: dict[str, int | str] = {
            "kód obce": code,
            "název obce": name,
            "voliči v seznamu": voters,
            "vydané obálky": envelopes,
            "platné hlasy": valid,
        }
        for party in party_order:
            row[party] = party_votes.get(party, 0)
        rows.append(row)

    write_csv(output_file, rows, party_order)
    print(f"Done. Saved {len(rows)} municipalities to {output_file}")


def main() -> None:
    """CLI entrypoint."""
    district_url, output_file = parse_args(sys.argv)
    scrape(district_url, output_file)


if __name__ == "__main__":
    main()
