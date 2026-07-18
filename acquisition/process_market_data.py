"""
acquisition/process_market_data.py

Cleans the raw fundamentals.json and news.json (yfinance semi-structured/
unstructured data) and saves processed versions, ready for MongoDB import.
Follows the same raw -> processed pattern as Eric's SEDAR+/company site scripts.
"""

import json
import os

RAW_FUNDAMENTALS = "data/raw/smartcentres/fundamentals.json"
RAW_NEWS = "data/raw/smartcentres/news.json"
PROCESSED_FOLDER = "data/processed/smartcentres"


def clean_fundamentals():
    with open(RAW_FUNDAMENTALS, "r", encoding="utf-8") as f:
        doc = json.load(f)

    if doc.get("company_id") != "smartcentres":
        print(f"WARNING: unexpected company_id in fundamentals: {doc.get('company_id')}")

    fundamentals = doc.get("fundamentals", {})
    before = len(fundamentals)
    cleaned = {k: v for k, v in fundamentals.items() if v is not None}
    removed = before - len(cleaned)
    if removed > 0:
        print(f"[fundamentals] Removed {removed} null fields ({before} -> {len(cleaned)})")

    doc["fundamentals"] = cleaned
    return doc


def clean_news():
    with open(RAW_NEWS, "r", encoding="utf-8") as f:
        headlines = json.load(f)

    before = len(headlines)
    seen = set()
    cleaned = []
    for item in headlines:
        headline_text = item.get("headline", "").strip()
        if not headline_text:
            continue
        if headline_text in seen:
            continue
        if item.get("company_id") != "smartcentres":
            print(f"WARNING: unexpected company_id in a news item: {item.get('company_id')}")
        seen.add(headline_text)
        cleaned.append(item)

    removed = before - len(cleaned)
    if removed > 0:
        print(f"[news] Removed {removed} empty/duplicate headlines ({before} -> {len(cleaned)})")

    return cleaned


def main():
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

    fundamentals_clean = clean_fundamentals()
    with open(f"{PROCESSED_FOLDER}/fundamentals_clean.json", "w", encoding="utf-8") as f:
        json.dump(fundamentals_clean, f, indent=2, ensure_ascii=False)
    print(f"Saved: {PROCESSED_FOLDER}/fundamentals_clean.json")

    news_clean = clean_news()
    with open(f"{PROCESSED_FOLDER}/news_clean.json", "w", encoding="utf-8") as f:
        json.dump(news_clean, f, indent=2, ensure_ascii=False)
    print(f"Saved: {PROCESSED_FOLDER}/news_clean.json ({len(news_clean)} headlines)")


if __name__ == "__main__":
    main()