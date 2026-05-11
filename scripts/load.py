import pandas as pd
from pathlib import Path
from datetime import datetime
from sqlalchemy import text
from db_connection import get_engine

TODAY   = datetime.today().strftime("%Y-%m-%d")
STAGING = Path(__file__).parent.parent / "data" / "staging"
engine  = get_engine()

# ── Helper: upsert using MERGE ───────────────────────────────
def upsert(df, table, match_col):
    staging_table = f"stg_{table}"

    # Build column definitions for CREATE TABLE
    type_map = {
        "object":   "NVARCHAR(500)",
        "int64":    "BIGINT",
        "int32":    "INT",
        "float64":  "FLOAT",
        "bool":     "BIT",
        "datetime64[ns]": "DATETIME",
    }

    col_defs = ", ".join([
        f"[{col}] {type_map.get(str(df[col].dtype), 'NVARCHAR(500)')}"
        for col in df.columns
    ])

    with engine.begin() as conn:
        # Step 1: drop staging table if it exists from a previous failed run
        conn.execute(text(f"IF OBJECT_ID('{staging_table}') IS NOT NULL DROP TABLE {staging_table}"))

        # Step 2: create staging table
        conn.execute(text(f"CREATE TABLE {staging_table} ({col_defs})"))

        # Step 3: insert rows one batch at a time
        rows = df.where(pd.notna(df), other=None).values.tolist()
        placeholders = ", ".join(["?" for _ in df.columns])
        raw_conn = conn.connection  # get the underlying pyodbc connection
        cursor = raw_conn.cursor()
        cursor.fast_executemany = True
        cursor.executemany(
            f"INSERT INTO {staging_table} VALUES ({placeholders})",
            rows
        )
        cursor.commit()

        # Step 4: MERGE into target table
        cols        = ", ".join([f"[{c}]" for c in df.columns])
        update_cols = ", ".join([f"t.[{c}] = s.[{c}]" for c in df.columns if c != match_col])
        insert_vals = ", ".join([f"s.[{c}]" for c in df.columns])

        conn.execute(text(f"""
            MERGE [{table}] AS t
            USING [{staging_table}] AS s
            ON t.[{match_col}] = s.[{match_col}]
            WHEN MATCHED THEN UPDATE SET {update_cols}
            WHEN NOT MATCHED THEN INSERT ({cols}) VALUES ({insert_vals});
        """))

        # Step 5: clean up
        conn.execute(text(f"DROP TABLE {staging_table}"))

    print(f"  Upserted {len(df)} rows into {table}")

# ── 1. Load dim_geography from countries.json ────────────────
import json
countries_path = Path(__file__).parent.parent / "data" / "landing" / "countries.json"
with open(countries_path) as f:
    countries = json.load(f)

geo_df = pd.DataFrame(countries)[["name","region","subregion","currency"]]
geo_df.columns = ["country","region","subregion","currency"]
upsert(geo_df, "dim_geography", "country")

# ── 2. Load dim_product ──────────────────────────────────────
product_df = pd.read_parquet(STAGING / "dim_product.parquet")[
    ["product_name", "product_category"]
]
upsert(product_df, "dim_product", "product_name")

# ── 3. Load dim_customer ─────────────────────────────────────
customer_df = pd.read_parquet(STAGING / "dim_customer.parquet")[
    ["customer_id","customer_name","email","country","currency"]
]
upsert(customer_df, "dim_customer", "customer_id")

# ── 4. Load dim_date ─────────────────────────────────────────
order_df = pd.read_parquet(STAGING / "fact_orders.parquet")
dates = pd.to_datetime(order_df["order_date"]).dt.normalize().unique()
date_rows = []
for d in sorted(dates):
    date_rows.append({
        "date_key":    int(d.strftime("%Y%m%d")),
        "full_date":   d.date(),
        "year":        d.year,
        "quarter":     d.quarter,
        "month":       d.month,
        "month_name":  d.strftime("%B"),
        "week_number": d.isocalendar()[1],
        "day_of_week": d.dayofweek,
        "day_name":    d.strftime("%A"),
        "is_weekend":  int(d.dayofweek >= 5),
    })
date_df = pd.DataFrame(date_rows)
upsert(date_df, "dim_date", "date_key")

# ── 5. Load fact_orders ──────────────────────────────────────
# Fetch surrogate keys from SQL to replace name-based columns
def read_table(query):
    """Read a SQL query into a DataFrame without using pd.read_sql."""
    with engine.begin() as conn:
        cursor = conn.connection.cursor()
        cursor.execute(query)
        cols = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
    return pd.DataFrame.from_records(rows, columns=cols)

cust_map = read_table("SELECT customer_id, customer_key FROM dim_customer")
prod_map = read_table("SELECT product_name, product_key FROM dim_product")
geo_map  = read_table("SELECT country, geography_key FROM dim_geography")

order_df = pd.read_parquet(STAGING / "fact_orders.parquet")
order_df["order_date"] = pd.to_datetime(order_df["order_date"])
order_df["date_key"]   = order_df["order_date"].dt.strftime("%Y%m%d").astype(int)
order_df = order_df.merge(cust_map, on="customer_id", how="left")
order_df = order_df.merge(prod_map, on="product_name", how="left")
order_df = order_df.merge(geo_map,  on="country",      how="left")

fact_orders_df = order_df[[
    "order_id","customer_key","product_key","geography_key","date_key",
    "quantity","unit_price","total_order_value","total_order_value_usd",
    "currency","status","is_returned"
]]
upsert(fact_orders_df, "fact_orders", "order_id")

# ── 6. Load fact_returns ─────────────────────────────────────
ret_df = pd.read_parquet(STAGING / "fact_returns.parquet")
ret_df["order_date"] = pd.to_datetime(ret_df["order_date"])
ret_df["date_key"]   = ret_df["order_date"].dt.strftime("%Y%m%d").astype(int)
ret_df = ret_df.merge(cust_map, on="customer_id", how="left")
ret_df = ret_df.merge(prod_map, on="product_name", how="left")
ret_df = ret_df.merge(geo_map,  on="country",      how="left")

fact_returns_df = ret_df[[
    "order_id","customer_key","product_key","geography_key","date_key",
    "total_order_value_usd"
]]
upsert(fact_returns_df, "fact_returns", "order_id")

print("\nAll tables loaded successfully!")