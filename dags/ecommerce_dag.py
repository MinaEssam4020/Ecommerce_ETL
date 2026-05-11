from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import sys

PROJECT = "/home/mina/airflow-project/data-engineering-project"  


default_args = {
    "owner":            "mina",
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,   # set to True + add email config later
}

with DAG(
    dag_id="ecommerce_pipeline",
    default_args=default_args,
    description="Daily e-commerce sales pipeline",
    schedule_interval="0 0 * * *",   
    start_date=datetime(2026, 1, 1),
    catchup=False,                   
    tags=["ecommerce", "sales"],
) as dag:

    def run_script(script_name):
        
        result = subprocess.run(
            [sys.executable, f"{PROJECT}/scripts/{script_name}"],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            raise Exception(f"{script_name} failed:\n{result.stderr}")

    # ── Task 1: Ingest ───────────────────────────────────────
    def ingest():
        run_script("generate_orders.py")
        run_script("fetch_reference_data.py")

    task_ingest = PythonOperator(
        task_id="ingest",
        python_callable=ingest,
    )

    # ── Task 2: Transform ────────────────────────────────────
    def transform():
        run_script("transform.py")

    task_transform = PythonOperator(
        task_id="transform",
        python_callable=transform,
    )

    # ── Task 3: Quality check ────────────────────────────────
    def quality_check():
        import pandas as pd
        from pathlib import Path

        staging = Path(PROJECT) / "data" / "staging"
        checks_passed = True

        for fname in ["fact_orders.parquet", "fact_returns.parquet",
                      "dim_customer.parquet", "dim_product.parquet"]:
            df = pd.read_parquet(staging / fname)
            if len(df) == 0:
                print(f"FAIL: {fname} is empty")
                checks_passed = False
            else:
                print(f"OK:   {fname} has {len(df)} rows")

        orders = pd.read_parquet(staging / "fact_orders.parquet")
        nulls = orders["order_id"].isna().sum()
        if nulls > 0:
            print(f"FAIL: {nulls} null order_ids found")
            checks_passed = False

        neg = (orders["total_order_value_usd"] <= 0).sum()
        if neg > 0:
            print(f"FAIL: {neg} orders with zero or negative USD value")
            checks_passed = False

        if not checks_passed:
            raise Exception("Quality checks failed — load aborted")
        print("All quality checks passed!")

    task_quality = PythonOperator(
        task_id="quality_check",
        python_callable=quality_check,
    )

    # ── Task 4: Load ─────────────────────────────────────────
    def load():
        run_script("load.py")

    task_load = PythonOperator(
        task_id="load",
        python_callable=load,
    )

    # ── Set the order ────────────────────────────────────────
    task_ingest >> task_transform >> task_quality >> task_load