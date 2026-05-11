import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import os

PROJECT_ROOT = Path(__file__).parent.parent
LANDING_DIR = PROJECT_ROOT / "data" / "landing"
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

COUNTRIES = [
    {"name": "United States", "cca2": "US", "region": "Americas", "subregion": "Northern America", "currency": "USD"},
    {"name": "United Kingdom", "cca2": "GB", "region": "Europe",   "subregion": "Northern Europe",  "currency": "GBP"},
    {"name": "Germany",        "cca2": "DE", "region": "Europe",   "subregion": "Western Europe",   "currency": "EUR"},
    {"name": "France",         "cca2": "FR", "region": "Europe",   "subregion": "Western Europe",   "currency": "EUR"},
    {"name": "Japan",          "cca2": "JP", "region": "Asia",     "subregion": "Eastern Asia",     "currency": "JPY"},
    {"name": "China",          "cca2": "CN", "region": "Asia",     "subregion": "Eastern Asia",     "currency": "CNY"},
    {"name": "India",          "cca2": "IN", "region": "Asia",     "subregion": "Southern Asia",    "currency": "INR"},
    {"name": "Brazil",         "cca2": "BR", "region": "Americas", "subregion": "South America",    "currency": "BRL"},
    {"name": "Canada",         "cca2": "CA", "region": "Americas", "subregion": "Northern America", "currency": "CAD"},
    {"name": "Australia",      "cca2": "AU", "region": "Oceania",  "subregion": "Australia",        "currency": "AUD"},
    {"name": "Egypt",          "cca2": "EG", "region": "Africa",   "subregion": "Northern Africa",  "currency": "EGP"},
    {"name": "South Africa",   "cca2": "ZA", "region": "Africa",   "subregion": "Southern Africa",  "currency": "ZAR"},
    {"name": "Mexico",         "cca2": "MX", "region": "Americas", "subregion": "Central America",  "currency": "MXN"},
    {"name": "Italy",          "cca2": "IT", "region": "Europe",   "subregion": "Southern Europe",  "currency": "EUR"},
    {"name": "Spain",          "cca2": "ES", "region": "Europe",   "subregion": "Southern Europe",  "currency": "EUR"},
    {"name": "South Korea",    "cca2": "KR", "region": "Asia",     "subregion": "Eastern Asia",     "currency": "KRW"},
    {"name": "Netherlands",    "cca2": "NL", "region": "Europe",   "subregion": "Western Europe",   "currency": "EUR"},
    {"name": "Saudi Arabia",   "cca2": "SA", "region": "Asia",     "subregion": "Western Asia",     "currency": "SAR"},
    {"name": "UAE",            "cca2": "AE", "region": "Asia",     "subregion": "Western Asia",     "currency": "AED"},
    {"name": "Nigeria",        "cca2": "NG", "region": "Africa",   "subregion": "Western Africa",   "currency": "NGN"},
]

def fetch_countries():
    LANDING_DIR.mkdir(parents=True, exist_ok=True)
    out_path = LANDING_DIR / "countries.json"
    with open(out_path, "w") as f:
        json.dump(COUNTRIES, f, indent=2)
    print(f"Saved {len(COUNTRIES)} countries to {out_path}")

def fetch_fx_rates():
    key = os.getenv("OPEN_EXCHANGE_RATES_KEY")
    if not key:
        print("ERROR: OPEN_EXCHANGE_RATES_KEY not found in .env")
        return

    url = f"https://openexchangerates.org/api/latest.json?app_id={key}&base=USD"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    today = datetime.today().strftime("%Y-%m-%d")
    out_path = LANDING_DIR / f"fx_rates_{today}.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved FX rates for {len(data['rates'])} currencies to {out_path}")

if __name__ == "__main__":
    fetch_countries()
    fetch_fx_rates()