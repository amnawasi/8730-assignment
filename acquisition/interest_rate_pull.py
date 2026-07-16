"""
BSMM-8730 — Smart Centres REIT Analysis
Script: Interest Rate Data Collection
Author: Muhammad Ahmad
Role: Member C — Bank of Canada Valet API
Date: July 2026

What this script does:
- Connects to the Bank of Canada Valet API
- Downloads the overnight interest rate history (2020 to 2026)
- Saves the data as a CSV file
- Falls back to a small sample if the live API call fails, so the rest
  of the pipeline can still run and be tested

Data Source:
- API: Bank of Canada Valet API
- URL: https://www.bankofcanada.ca/valet-api-how-to/
- Series V39079 = Overnight Money Market Financing Rate
- Frequency: Daily
"""

import requests
import pandas as pd
import os

START_DATE  = "2020-01-01"
END_DATE    = "2026-07-07"
RATE_SERIES = "V39079"
OUTPUT_FILE = "data/raw/bank_of_canada/overnight_rate.csv"


def get_overnight_rate(start=START_DATE, end=END_DATE, series=RATE_SERIES):
    """
    Pulls daily overnight rate data from the Bank of Canada Valet API.
    Returns a structured DataFrame with date + overnight_rate_pct columns.
    Falls back to a small hardcoded sample if the live call fails.
    """
    api_url = (
        f"https://www.bankofcanada.ca/valet/observations/{series}/json"
        f"?start_date={start}&end_date={end}"
    )

    try:
        print("Calling Bank of Canada API for interest rate data...")
        print(f"URL: {api_url}")

        response = requests.get(api_url, timeout=10)

        if response.status_code != 200:
            raise ValueError(f"API returned status code {response.status_code}")

        data         = response.json()
        observations = data["observations"]

        print(f"Total observations received: {len(observations)}")

        rows = []
        for obs in observations:
            date  = obs["d"]
            value = obs.get(series, {}).get("v", None)
            rows.append({"date": date, "overnight_rate_pct": value})

        df = pd.DataFrame(rows)
        df["date"]               = pd.to_datetime(df["date"])
        df["overnight_rate_pct"] = pd.to_numeric(df["overnight_rate_pct"], errors="coerce")

        print(f"[overnight_rate] Pulled {len(df)} rows ({start} to {end})")
        return df

    except Exception as e:
        print(f"[overnight_rate] Live pull failed ({e}) - returning fallback sample")

        fallback_rows = [
            {"date": "2020-01-02", "overnight_rate_pct": 1.75},
            {"date": "2022-07-13", "overnight_rate_pct": 2.50},
            {"date": "2023-07-12", "overnight_rate_pct": 5.00},
            {"date": "2025-01-29", "overnight_rate_pct": 3.00},
            {"date": "2026-07-07", "overnight_rate_pct": 2.25},
        ]
        df = pd.DataFrame(fallback_rows)
        df["date"] = pd.to_datetime(df["date"])
        return df


def validate_and_save(df, output_file=OUTPUT_FILE):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print()
    print("=== Interest Rate Data Summary ===")
    print(f"  Date range    : {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"  Total rows    : {len(df)}")
    print(f"  Missing values: {df.isnull().sum().sum()}")
    print(f"  Lowest rate   : {df['overnight_rate_pct'].min()}%")
    print(f"  Highest rate  : {df['overnight_rate_pct'].max()}%")
    print(f"  Average rate  : {df['overnight_rate_pct'].mean():.2f}%")

    df.to_csv(output_file, index=False)

    print()
    print(f"Saved: {output_file}")
    print(f"Rows : {len(df)}")


if __name__ == "__main__":
    rate_df = get_overnight_rate()
    validate_and_save(rate_df)
    print()
    print("Done! Interest rate data collection complete.")
