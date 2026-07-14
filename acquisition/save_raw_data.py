"""
acquisition/save_raw_data.py

Runs the acquisition functions from yfinance_pull.py and wowa_scraping.py
and saves their output directly to data/raw/, with no cleaning applied.
Cleaning happens separately, as a joint group session, once all raw data
has been collected from every source.
"""

import os
import json

from yfinance_pull import get_price_history, get_fundamentals, get_news
from wowa_scraping import get_reit_types, get_current_peer_metrics

RAW_SMARTCENTRES = "data/raw/smartcentres"
RAW_PEERS = "data/raw/peers"

for folder in [RAW_SMARTCENTRES, RAW_PEERS]:
    os.makedirs(folder, exist_ok=True)


def save_raw_data():
    price_df = get_price_history()
    fundamentals_doc = get_fundamentals()
    news_docs = get_news()
    wowa_df = get_reit_types()
    peer_df = get_current_peer_metrics()

    price_df.to_csv(f"{RAW_SMARTCENTRES}/price_history.csv", index=False)
    with open(f"{RAW_SMARTCENTRES}/fundamentals.json", "w") as f:
        json.dump(fundamentals_doc, f, indent=2, default=str)
    with open(f"{RAW_SMARTCENTRES}/news.json", "w") as f:
        json.dump(news_docs, f, indent=2, default=str)

    wowa_df.to_csv(f"{RAW_PEERS}/wowa_reit_types.csv", index=False)
    peer_df.to_csv(f"{RAW_PEERS}/peer_metrics.csv", index=False)

    print("[save_raw_data] Saved 5 raw files:")
    print(f"  {RAW_SMARTCENTRES}/price_history.csv")
    print(f"  {RAW_SMARTCENTRES}/fundamentals.json")
    print(f"  {RAW_SMARTCENTRES}/news.json")
    print(f"  {RAW_PEERS}/wowa_reit_types.csv")
    print(f"  {RAW_PEERS}/peer_metrics.csv")


if __name__ == "__main__":
    save_raw_data()