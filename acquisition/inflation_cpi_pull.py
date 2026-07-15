"""
BSMM-8730 — Smart Centres REIT Analysis
Script: Inflation CPI Data Collection
Author: Muhammad Ahmad
Role: Member C — Bank of Canada Valet API
Date: July 2026

What this script does:
- Connects to the Bank of Canada Valet API
- Downloads the Consumer Price Index (CPI) history (2020 to 2025)
- Saves the data as a CSV file

What is CPI and why does it matter?
CPI = Consumer Price Index.
Think of it as a basket of everyday goods like groceries, gas, and rent.
When the CPI number goes up, those things cost more — that is inflation.
High inflation caused the Bank of Canada to raise interest rates in 2022-2023,
which directly hurt Smart Centres REIT stock price.

Data Source:
- API: Bank of Canada Valet API
- URL: https://www.bankofcanada.ca/valet-api-how-to/
- Series V41690973 = Consumer Price Index (CPI)
- Frequency: Monthly (one reading per month)
"""

import requests
import pandas as pd
import os

# ============================================================
# SETTINGS
# ============================================================

START_DATE        = "2020-01-01"
END_DATE          = "2025-12-31"
INFLATION_SERIES  = "V41690973"

API_URL = (
    f"https://www.bankofcanada.ca/valet/observations/{INFLATION_SERIES}/json"
    f"?start_date={START_DATE}&end_date={END_DATE}"
)

OUTPUT_FILE = "data/raw/bank_of_canada/inflation_cpi.csv"

# ============================================================
# STEP 1 — Create Output Folder
# ============================================================

os.makedirs("data/raw/bank_of_canada", exist_ok=True)
print("Output folder ready: data/raw/bank_of_canada/")
print()
print("Note: CPI data is monthly so expect around 60-70 rows total.")
print("That is completely normal — one reading per month.")

# ============================================================
# STEP 2 — Call the API
# ============================================================

print()
print("Calling Bank of Canada API for inflation (CPI) data...")
print(f"URL: {API_URL}")
print()

response = requests.get(API_URL)

if response.status_code == 200:
    print(f"Success! Status code: {response.status_code}")
else:
    print(f"Error. Status code: {response.status_code}")
    print("Check your internet connection and try again.")
    exit()

# ============================================================
# STEP 3 — Parse the Response
# ============================================================

data         = response.json()
observations = data["observations"]

print(f"Total observations received: {len(observations)}")
print()
print("Example raw observation:")
print(observations[0])
print()

# Extract date and CPI value from each observation
rows = []
for obs in observations:
    date  = obs["d"]
    value = obs.get(INFLATION_SERIES, {}).get("v", None)
    rows.append({"date": date, "cpi_value": value})

# Convert to DataFrame
df = pd.DataFrame(rows)

# Fix data types
df["date"]      = pd.to_datetime(df["date"])
df["cpi_value"] = pd.to_numeric(df["cpi_value"], errors="coerce")

print(f"Rows extracted: {len(df)}")
print()
print(df.head(10).to_string(index=False))

# ============================================================
# STEP 4 — Validate the Data
# ============================================================

print()
print("=== Inflation (CPI) Data Summary ===")
print(f"  Date range    : {df['date'].min().date()} to {df['date'].max().date()}")
print(f"  Total rows    : {len(df)}")
print(f"  Missing values: {df.isnull().sum().sum()}")
print(f"  Lowest CPI    : {df['cpi_value'].min()}")
print(f"  Highest CPI   : {df['cpi_value'].max()}")
print()
print("What the CPI number means:")
print("  CPI represents a basket of everyday goods priced at 100 in a base year.")
print("  A CPI of 150 means those goods now cost 50% more than the base year.")
print("  Rising CPI = rising inflation = pressure on Bank of Canada to raise rates.")

# ============================================================
# STEP 5 — Save as CSV
# ============================================================

df.to_csv(OUTPUT_FILE, index=False)

print()
print(f"Saved: {OUTPUT_FILE}")
print(f"Rows : {len(df)}")
print()
print("Done! Inflation CPI data collection complete.")
