import json
import random
from datetime import datetime
from faker import Faker
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
LANDING_DIR = PROJECT_ROOT / "data" / "landing"
fake = Faker()
COUNTRIES = [
    {"name": "United States",  "currency": "USD"},
    {"name": "United Kingdom", "currency": "GBP"},
    {"name": "Germany",        "currency": "EUR"},
    {"name": "France",         "currency": "EUR"},
    {"name": "Japan",          "currency": "JPY"},
    {"name": "China",          "currency": "CNY"},
    {"name": "India",          "currency": "INR"},
    {"name": "Brazil",         "currency": "BRL"},
    {"name": "Canada",         "currency": "CAD"},
    {"name": "Australia",      "currency": "AUD"},
    {"name": "Egypt",          "currency": "EGP"},
    {"name": "South Africa",   "currency": "ZAR"},
    {"name": "Mexico",         "currency": "MXN"},
    {"name": "Italy",          "currency": "EUR"},
    {"name": "Spain",          "currency": "EUR"},
    {"name": "South Korea",    "currency": "KRW"},
    {"name": "Netherlands",    "currency": "EUR"},
    {"name": "Saudi Arabia",   "currency": "SAR"},
    {"name": "UAE",            "currency": "AED"},
    {"name": "Nigeria",        "currency": "NGN"},
]

CATEGORIES = {
    "Electronics":   ["Laptop", "Phone", "Tablet", "Headphones", "Charger"],
    "Clothing":      ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress"],
    "Home & Garden": ["Lamp", "Plant Pot", "Pillow", "Rug", "Candle"],
    "Sports":        ["Yoga Mat", "Dumbbells", "Water Bottle", "Shorts"],
    "Books":         ["Novel", "Cookbook", "Textbook", "Biography"],
}

STATUSES = ["completed", "completed", "completed", "returned", "pending"]

def generate_orders(n=1000, date=None):
    if date is None:
        date = datetime.today().strftime("%Y-%m-%d")

    orders = []
    for _ in range(n):
        category = random.choice(list(CATEGORIES.keys()))
        product  = random.choice(CATEGORIES[category])
        quantity = random.randint(1, 5)
        price    = round(random.uniform(5.0, 500.0), 2)
        country  = random.choice(COUNTRIES)
        orders.append({
            "order_id":        fake.uuid4(),
            "customer_id":     fake.uuid4(),
            "customer_name":   fake.name(),
            "email":           fake.email(),
            "country":         country["name"],
            "currency":        country["currency"],
            "city":            fake.city(),
            "product_category": category,
            "product_name":    product,
            "quantity":        quantity,
            "unit_price":      price,
            "order_date":      date,
            "status":          random.choice(STATUSES),
        })
    return orders

if __name__ == "__main__":
    today = datetime.today().strftime("%Y-%m-%d")
    orders = generate_orders(n=1000, date=today)

    LANDING_DIR.mkdir(parents=True, exist_ok=True)
    out_path = LANDING_DIR / f"orders_{today}.json"

    with open(out_path, "w") as f:
        json.dump(orders, f, indent=2)

    print(f"Saved {len(orders)} orders to {out_path}")