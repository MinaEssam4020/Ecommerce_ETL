import json
import pandas as pd
from pathlib import Path
from datetime import datetime

TODAY = datetime.today().strftime("%Y-%m-%d")
LANDING  = Path(__file__).parent.parent / "data" / "landing"
STAGING  = Path(__file__).parent.parent / "data" / "staging"
STAGING.mkdir(parents=True, exist_ok=True)


orders_path = LANDING / f"orders_{TODAY}.json"
with open(orders_path) as f:
    raw = json.load(f)

df = pd.DataFrame(raw)
print(f"Loaded {len(df)} raw orders")


df["order_date"] = pd.to_datetime(df["order_date"])


df["country"]          = df["country"].str.strip()
df["product_category"] = df["product_category"].str.strip()
df["product_name"]     = df["product_name"].str.strip()
df["status"]           = df["status"].str.lower().str.strip()
df["email"]            = df["email"].str.lower().str.strip()


before = len(df)
df = df.dropna(subset=["order_id", "customer_id", "country", "unit_price"])
print(f"Dropped {before - len(df)} rows with missing critical fields")


df = df.drop_duplicates(subset=["order_id"])
print(f"Rows after dedup: {len(df)}")

fx_path = LANDING / f"fx_rates_{TODAY}.json"
with open(fx_path) as f:
    fx_data = json.load(f)

fx_rates = fx_data["rates"]  


df["total_order_value"] = (df["quantity"] * df["unit_price"]).round(2)


df["total_order_value_usd"] = df.apply(
    lambda row: round(
        row["total_order_value"] / fx_rates.get(row["currency"], 1.0), 2
    ),
    axis=1
)


df["is_returned"] = df["status"] == "returned"

print(f"\nSample of computed columns:")
print(df[["order_id", "currency", "total_order_value",
          "total_order_value_usd", "is_returned"]].head(3))


dim_customer = (
    df[["customer_id", "customer_name", "email", "country", "currency"]]
    .drop_duplicates(subset=["customer_id"])
    .reset_index(drop=True)
)
dim_customer.to_parquet(STAGING / "dim_customer.parquet", index=False)
print(f"\ndim_customer:  {len(dim_customer)} rows")

dim_product = (
    df[["product_name", "product_category"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

dim_product.insert(0, "product_id", range(1, len(dim_product) + 1))
dim_product.to_parquet(STAGING / "dim_product.parquet", index=False)
print(f"dim_product:   {len(dim_product)} rows")


fact_orders = df[[
    "order_id", "customer_id", "product_name","country",
    "quantity", "unit_price",
    "total_order_value", "total_order_value_usd",
    "currency", "order_date", "status", "is_returned"
]].copy()
fact_orders.to_parquet(STAGING / "fact_orders.parquet", index=False)
print(f"fact_orders:   {len(fact_orders)} rows")


fact_returns = (
    df[df["is_returned"] == True][[
        "order_id", "customer_id", "product_name",
        "total_order_value_usd", "order_date", "country"
    ]]
    .copy()
    .reset_index(drop=True)
)
fact_returns.to_parquet(STAGING / "fact_returns.parquet", index=False)
print(f"fact_returns:  {len(fact_returns)} rows")

print("\nAll staging files saved to data/staging/")

