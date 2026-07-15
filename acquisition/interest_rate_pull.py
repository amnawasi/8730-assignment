"""
BSMM-8730 — Smart Centres REIT Analysis
Script: Interest Rate Data Collection
Author: Muhammad Ahmad
Role: Member C — Bank of Canada Valet API
Date: July 2026

What this script does:
- Connects to the Bank of Canada Valet API
- Downloads the overnight interest rate history (2020 to 2025)
- Saves the data as a CSV file

Data Source:
- API: Bank of Canada Valet API
- URL: https://www.bankofcanada.ca/valet-api-how-to/
- Series V39079 = Overnight Money Market Financing Rate
- Frequency: Daily
"""

import requests
import pandas as pd
import os

# ============================================================
# SETTINGS
# ============================================================

START_DATE  = "2020-01-01"
END_DATE    = "2025-12-31"
RATE_SERIES = "V39079"

API_URL = (
    f"https://www.bankofcanada.ca/valet/observations/{RATE_SERIES}/json"
    f"?start_date={START_DATE}&end_date={END_DATE}"
)

OUTPUT_FILE = "data/raw/bank_of_canada/overnight_rate.csv"

# ============================================================
# STEP 1 — Create Output Folder
# ============================================================

os.makedirs("data/raw/bank_of_canada", exist_ok=True)
print("Output folder ready: data/raw/bank_of_canada/")

# ============================================================
# STEP 2 — Call the API
# ============================================================

print()
print("Calling Bank of Canada API for interest rate data...")
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

# Extract date and rate value from each observation
rows = []
for obs in observations:
    date  = obs["d"]
    value = obs.get(RATE_SERIES, {}).get("v", None)
    rows.append({"date": date, "overnight_rate_pct": value})

# Convert to DataFrame
df = pd.DataFrame(rows)

# Fix data types
df["date"]               = pd.to_datetime(df["date"])
df["overnight_rate_pct"] = pd.to_numeric(df["overnight_rate_pct"], errors="coerce")

print(f"Rows extracted: {len(df)}")
print()
print(df.head(10).to_string(index=False))

# ============================================================
# STEP 4 — Validate the Data
# ============================================================

print()
print("=== Interest Rate Data Summary ===")
print(f"  Date range    : {df['date'].min().date()} to {df['date'].max().date()}")
print(f"  Total rows    : {len(df)}")
print(f"  Missing values: {df.isnull().sum().sum()}")
print(f"  Lowest rate   : {df['overnight_rate_pct'].min()}%")
print(f"  Highest rate  : {df['overnight_rate_pct'].max()}%")
print(f"  Average rate  : {df['overnight_rate_pct'].mean():.2f}%")

# ============================================================
# STEP 5 — Save as CSV
# ============================================================

df.to_csv(OUTPUT_FILE, index=False)

print()
print(f"Saved: {OUTPUT_FILE}")
print(f"Rows : {len(df)}")
print()
print("Done! Interest rate data collection complete.")
