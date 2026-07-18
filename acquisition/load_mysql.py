"""
acquisition/load_mysql.py

Loads all structured CSVs (price history, Bank of Canada rates, wowa.ca
REIT types, peer metrics) into MySQL. Tables are dropped and recreated
each run (idempotent - safe to re-run, same principle as delete_many()
in the MongoDB import scripts). Validation (row counts, date ranges,
null checks) happens as each table loads.
"""

import os
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

EXPECTED_START = "2020-01-01"
EXPECTED_END = "2026-07-07"


def get_connection():
    if not all([MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE]):
        raise ValueError("Missing MySQL credentials - check your .env file")
    return mysql.connector.connect(
        host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD
    )


def ensure_database(conn):
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
    conn.commit()
    cursor.execute(f"USE {MYSQL_DATABASE}")
    cursor.close()


def validate_dates(df, date_col, label):
    """Prints a warning if the date range doesn't match the group's fixed range."""
    if df.empty:
        print(f"  WARNING: {label} has no rows")
        return
    actual_start = df[date_col].min()
    actual_end = df[date_col].max()
    print(f"  Date range: {actual_start} to {actual_end}")
    if str(actual_start)[:10] > EXPECTED_START:
        print(f"  WARNING: {label} starts later than expected ({EXPECTED_START})")
    if str(actual_end)[:10] < "2026-06-01":  # loose check, some sources lag
        print(f"  NOTE: {label} ends earlier than the fixed cutoff - may be normal for slower-updating sources")


def load_price_history(conn):
    print("\n[price_history]")
    df = pd.read_csv("data/raw/smartcentres/price_history.csv")
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]

    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS price_history")
    cursor.execute("""
        CREATE TABLE price_history (
            date DATE,
            open DECIMAL(12,4),
            high DECIMAL(12,4),
            low DECIMAL(12,4),
            close DECIMAL(12,4),
            volume BIGINT,
            company_id VARCHAR(50),
            source VARCHAR(50),
            pulled_at DATETIME
        )
    """)

    nulls = df[["Open", "High", "Low", "Close"]].isnull().sum().sum()
    if nulls > 0:
        print(f"  WARNING: {nulls} null price values found")

    rows = [
        (
            str(row["Date"])[:10], row["Open"], row["High"], row["Low"], row["Close"],
            row["Volume"], row["company_id"], row["source"], row["pulled_at"]
        )
        for _, row in df.iterrows()
    ]
    cursor.executemany(
        "INSERT INTO price_history (date, open, high, low, close, volume, company_id, source, pulled_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        rows,
    )
    conn.commit()
    print(f"  Loaded {len(rows)} rows")
    validate_dates(df, "Date", "price_history")
    cursor.close()


def load_interest_rates(conn):
    print("\n[interest_rates]")
    df = pd.read_csv("data/raw/bank_of_canada/overnight_rate.csv")

    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS interest_rates")
    cursor.execute("""
        CREATE TABLE interest_rates (
            date DATE,
            overnight_rate_pct DECIMAL(6,3)
        )
    """)

    nulls = df["overnight_rate_pct"].isnull().sum()
    if nulls > 0:
        print(f"  WARNING: {nulls} null rate values found")

    rows = [(str(row["date"])[:10], row["overnight_rate_pct"]) for _, row in df.iterrows()]
    cursor.executemany("INSERT INTO interest_rates (date, overnight_rate_pct) VALUES (%s,%s)", rows)
    conn.commit()
    print(f"  Loaded {len(rows)} rows")
    validate_dates(df, "date", "interest_rates")
    cursor.close()


def load_inflation_cpi(conn):
    print("\n[inflation_cpi]")
    df = pd.read_csv("data/raw/bank_of_canada/inflation_cpi.csv")

    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS inflation_cpi")
    cursor.execute("""
        CREATE TABLE inflation_cpi (
            date DATE,
            cpi_value DECIMAL(8,2)
        )
    """)

    nulls = df["cpi_value"].isnull().sum()
    if nulls > 0:
        print(f"  WARNING: {nulls} null CPI values found")

    rows = [(str(row["date"])[:10], row["cpi_value"]) for _, row in df.iterrows()]
    cursor.executemany("INSERT INTO inflation_cpi (date, cpi_value) VALUES (%s,%s)", rows)
    conn.commit()
    print(f"  Loaded {len(rows)} rows")
    validate_dates(df, "date", "inflation_cpi")
    cursor.close()


def load_reit_types(conn):
    print("\n[reit_types]")
    df = pd.read_csv("data/raw/peers/wowa_reit_types.csv")

    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS reit_types")
    cursor.execute("""
        CREATE TABLE reit_types (
            reit_name VARCHAR(150),
            symbol VARCHAR(20),
            reit_type VARCHAR(100),
            source VARCHAR(50),
            pulled_at DATETIME,
            company_id VARCHAR(50)
        )
    """)

    rows = [
        (
            row["reit_name"], row["symbol"], row["reit_type"], row["source"],
            row["pulled_at"], row["company_id"] if pd.notnull(row["company_id"]) else None
        )
        for _, row in df.iterrows()
    ]
    cursor.executemany(
        "INSERT INTO reit_types (reit_name, symbol, reit_type, source, pulled_at, company_id) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        rows,
    )
    conn.commit()
    print(f"  Loaded {len(rows)} rows ({df['company_id'].notnull().sum()} tagged with company_id)")
    cursor.close()


def load_peer_metrics(conn):
    print("\n[peer_metrics]")
    df = pd.read_csv("data/raw/peers/peer_metrics.csv")

    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS peer_metrics")
    cursor.execute("""
        CREATE TABLE peer_metrics (
            company_id VARCHAR(50),
            symbol VARCHAR(20),
            current_price DECIMAL(12,4),
            dividend_yield DECIMAL(8,4),
            source VARCHAR(50),
            pulled_at DATETIME
        )
    """)

    nulls = df["current_price"].isnull().sum()
    if nulls > 0:
        print(f"  WARNING: {nulls} peer(s) missing current_price")

    rows = [
        (
            row["company_id"], row["symbol"], row["current_price"],
            row["dividend_yield"], row["source"], row["pulled_at"]
        )
        for _, row in df.iterrows()
    ]
    cursor.executemany(
        "INSERT INTO peer_metrics (company_id, symbol, current_price, dividend_yield, source, pulled_at) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        rows,
    )
    conn.commit()
    print(f"  Loaded {len(rows)} rows")
    cursor.close()


def main():
    conn = get_connection()
    try:
        ensure_database(conn)
        load_price_history(conn)
        load_interest_rates(conn)
        load_inflation_cpi(conn)
        load_reit_types(conn)
        load_peer_metrics(conn)
        print("\nAll tables loaded successfully.")
    except Exception as e:
        print(f"Load failed: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()