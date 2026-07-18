"""
acquisition/yfinance_pull.py

Pulls SmartCentres REIT (SRU-UN.TO) data from yfinance and splits it into
three pieces based on data type, per the project's structured/semi-structured/
unstructured framing:
  - price_history  -> structured  -> MySQL
  - fundamentals   -> semi-structured -> MongoDB
  - news           -> unstructured -> MongoDB

Uses a fixed date range (Jan 1, 2020 - Jul 7, 2026) so results are reproducible
across teammates and reruns, per the group's decision log.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

TICKER = "SRU-UN.TO"
COMPANY_ID = "smartcentres"
START_DATE = "2020-01-01"
END_DATE = "2026-07-07"  # fixed, per group decision - do NOT use datetime.today()


def get_price_history(ticker=TICKER, start=START_DATE, end=END_DATE):
    """
    Pulls daily price history. Returns a structured DataFrame -> MySQL.
    Falls back to an empty-but-correctly-shaped DataFrame on failure, so
    downstream code doesn't crash - it just has nothing to load.
    """
    try:
        tkr = yf.Ticker(ticker)
        df = tkr.history(start=start, end=end)
        if df.empty:
            raise ValueError("yfinance returned no price data")
        df = df.reset_index()
        df["company_id"] = COMPANY_ID
        df["source"] = "yfinance"
        df["pulled_at"] = datetime.now().isoformat()
        print(f"[price_history] Pulled {len(df)} rows for {ticker} ({start} to {end})")
        return df
    except Exception as e:
        print(f"[price_history] Live pull failed ({e}) - returning empty fallback")
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close",
                                      "Volume", "company_id", "source", "pulled_at"])


def get_fundamentals(ticker=TICKER):
    """
    Pulls the .info dict - nested, variable keys per ticker, the textbook
    semi-structured case. Returns a dict ready to insert as one MongoDB doc.
    """
    try:
        tkr = yf.Ticker(ticker)
        info = tkr.info
        if not info:
            raise ValueError("yfinance returned no fundamentals data")
        doc = {
            "company_id": COMPANY_ID,
            "ticker": ticker,
            "source": "yfinance",
            "pulled_at": datetime.now().isoformat(),
            "fundamentals": info,  # keep the nested dict as-is - this is the point of MongoDB
        }
        print(f"[fundamentals] Pulled {len(info)} fields for {ticker}")
        return doc
    except Exception as e:
        print(f"[fundamentals] Live pull failed ({e}) - returning empty fallback")
        return {
            "company_id": COMPANY_ID,
            "ticker": ticker,
            "source": "yfinance_fallback",
            "pulled_at": datetime.now().isoformat(),
            "fundamentals": {},
        }


def get_news(ticker=TICKER):
    """
    Pulls recent news headlines - unstructured text. Returns a list of
    dicts, one per headline, ready to insert into MongoDB.

    Note: yfinance nests news fields under a "content" key (title,
    provider.displayName, canonicalUrl.url) rather than at the top level -
    this was a source of a real bug caught during cleaning, where all
    headlines came back empty because the old code read top-level fields
    that no longer existed.
    """
    try:
        tkr = yf.Ticker(ticker)
        news_items = tkr.news
        if not news_items:
            raise ValueError("yfinance returned no news data")
        docs = []
        for item in news_items:
            content = item.get("content", item)  # fallback if structure changes again
            provider = content.get("provider", {})
            docs.append({
                "company_id": COMPANY_ID,
                "source": "yfinance_news",
                "headline": content.get("title", ""),
                "publisher": provider.get("displayName", "") if isinstance(provider, dict) else "",
                "link": content.get("canonicalUrl", {}).get("url", ""),
                "pulled_at": datetime.now().isoformat(),
            })
        print(f"[news] Pulled {len(docs)} headlines for {ticker}")
        return docs
    except Exception as e:
        print(f"[news] Live pull failed ({e}) - returning empty fallback")
        return []


if __name__ == "__main__":
    # Quick manual test when running this file directly - not the final
    # pipeline entry point, just lets you sanity-check each function works
    # before wiring it into cleaning/loading scripts.
    prices = get_price_history()
    print(prices.head())

    fundamentals = get_fundamentals()
    print(list(fundamentals["fundamentals"].keys())[:10])  # first 10 field names

    news = get_news()
    for n in news[:3]:
        print(n["headline"])