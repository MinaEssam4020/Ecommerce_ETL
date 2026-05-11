from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
import os
import urllib

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

def get_engine():
    server   = os.getenv("SQL_SERVER")
    database = os.getenv("SQL_DATABASE")

    params = urllib.parse.quote_plus(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={os.getenv('SQL_USER')};"
        f"PWD={os.getenv('SQL_PASSWORD')};"
    )
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    return engine

if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        print("Connected successfully!")