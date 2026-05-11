import json
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).parent.parent
LANDING_DIR = PROJECT_ROOT / "data" / "landing"

today = datetime.today().strftime("%Y-%m-%d")
checks = [
    LANDING_DIR / f"orders_{today}.json",
    LANDING_DIR / "countries.json",
    LANDING_DIR / f"fx_rates_{today}.json",
]
all_good = True
for path_str in checks:
    path = Path(path_str)
    if not path.exists():
        print(f"MISSING: {path_str}")
        all_good = False
    else:
        with open(path) as f:
            data = json.load(f)
        count = len(data) if isinstance(data, list) else len(data.get("rates", {}))
        print(f"OK  {path_str}  ({count} records)")

print("\nAll checks passed!" if all_good else "\nSome files are missing.")