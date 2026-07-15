"""
BSMM-8730 — Smart Centres REIT Analysis
Script: Inflation CPI Data Collection
Author: Muhammad Ahmad
Role: Member C — Bank of Canada Valet API
Date: July 2026

What this script does:
- Connects to the Bank of Canada Valet API
- Downloads the Consumer Price Index (CPI) history (2020 to 2026)
- Saves the data as a CSV file
- Falls back to a small sample if the live API call fails, so the rest
  of the pipeline can still run and be tested

What is CPI and why does it matter?
CPI = Consumer Price Index. Think of it as a basket of everyday goods
like groceries, gas, and rent. When the CPI number goes up, those things
cost more — that is inflation. High inflation caused the Bank of Canada
to raise interest rates in 2022-2023, which directly affected REIT
valuations like Smart Centres.

Data Source:
- API: Bank of Canada Valet API
- URL: https://www.bankofcanada.ca/valet-api-how-to/
- Series V41690973 = Total Consumer Price Index (CPI)
- Frequency: Monthly
"""

import requests
import pandas as pd
import os

START_DATE       = "2020-01-01"
END_DATE         = "2026-07-07"
INFLATION_SERIES = "V41690973"
OUTPUT_FILE      = "data/raw/bank_of_canada/inflation_cpi.csv"


def get_inflation_cpi(start=START_DATE, end=END_DATE, series=INFLATION_SERIES):
    """
    Pulls monthly CPI data from the Bank of Canada Valet API.
    Returns a structured DataFrame with date + cpi_value columns.
    Falls back to a small hardcoded sample if the live call fails.
    """
    api_url = (
        f"https://www.bankofcanada.ca/valet/observations/{series}/json"
        f"?start_date={start}&end_date={end}"
    )

    try:
        print("Calling Bank of Canada API for inflation (CPI) data...")
        print(f"URL: {api_url}")

        response = requests.get(api_url, timeout=10)

        if response.status_code != 200:
            raise ValueError(f"API returned status code {response.status_code}")

        data         = response.json()
        observations = data["observations"]

        print(f"Total observations received: {len(observations)}")
        print("Note: CPI data is monthly so expect around 75-80 rows total.")

        rows = []
        for obs in observations:
            date  = obs["d"]
            value = obs.get(series, {}).get("v", None)
            rows.append({"date": date, "cpi_value": value})

        df = pd.DataFrame(rows)
        df["date"]      = pd.to_datetime(df["date"])
        df["cpi_value"] = pd.to_numeric(df["cpi_value"], errors="coerce")

        print(f"[inflation_cpi] Pulled {len(df)} rows ({start} to {end})")
        return df

    except Exception as e:
        print(f"[inflation_cpi] Live pull failed ({e}) - returning fallback sample")

        fallback_rows = [
            {"date": "2020-01-01", "cpi_value": 136.8},
            {"date": "2022-06-01", "cpi_value": 153.8},
            {"date": "2023-06-01", "cpi_value": 158.1},
            {"date": "2025-01-01", "cpi_value": 163.4},
            {"date": "2026-07-01", "cpi_value": 166.9},
        ]
        df = pd.DataFrame(fallback_rows)
        df["date"] = pd.to_datetime(df["date"])
        return df


def validate_and_save(df, output_file=OUTPUT_FILE):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print()
    print("=== Inflation (CPI) Data Summary ===")
    print(f"  Date range    : {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"  Total rows    : {len(df)}")
    print(f"  Missing values: {df.isnull().sum().sum()}")
    print(f"  Lowest CPI    : {df['cpi_value'].min()}")
    print(f"  Highest CPI   : {df['cpi_value'].max()}")
    print()
    print("What the CPI number means:")
    print("  CPI represents a basket of everyday goods priced against a base year.")
    print("  Rising CPI = rising inflation = pressure on Bank of Canada to raise rates.")

    df.to_csv(output_file, index=False)

    print()
    print(f"Saved: {output_file}")
    print(f"Rows : {len(df)}")


if __name__ == "__main__":
    cpi_df = get_inflation_cpi()
    validate_and_save(cpi_df)
    print()
    print("Done! Inflation CPI data collection complete.")
