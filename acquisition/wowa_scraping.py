"""
acquisition/wowa_scraping.py

Scrapes the Canadian REIT comparison table from wowa.ca/reit-canada.
Note: the price/yield figures on this page are dated (last updated Aug 2021
per the page itself) - not safe to use as current data. This script pulls
REIT Type/sector categorization from wowa.ca (stable, doesn't go stale), and
current share price + dividend yield for each peer from yfinance instead.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
from datetime import datetime

URL = "https://wowa.ca/reit-canada"
COMPANY_ID = "smartcentres"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

# Peers to compare against - chosen to match your assignment's suggested
# competitors, keeping it to a manageable set rather than all 34 REITs
# on the wowa.ca page
PEER_TICKERS = {
    "smartcentres": "SRU-UN.TO",
    "riocan": "REI-UN.TO",
    "ct_reit": "CRT-UN.TO",
    "choice_properties": "CHP-UN.TO",
}


def get_reit_types(url=URL):
    """
    Scrapes REIT name, symbol, and Type from wowa.ca. Type (e.g. "Retail",
    "Residential") is stable sector categorization - unlike price/yield,
    it doesn't go stale, so it's safe to use even from an older page.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if table is None:
            raise ValueError("No table found on the page")

        rows = []
        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cells) < 6:
                continue  # skip malformed rows
            # Real columns: REIT, Symbol, Type, Share Price, Market Cap, Yield
            reit_name, symbol, reit_type = cells[0], cells[1], cells[2]
            rows.append([reit_name, symbol, reit_type])

        if not rows:
            raise ValueError("Table found but no data rows extracted")

        df = pd.DataFrame(rows, columns=["reit_name", "symbol", "reit_type"])
        df["source"] = "wowa.ca"
        df["pulled_at"] = datetime.now().isoformat()
        df["company_id"] = df["symbol"].apply(
            lambda s: COMPANY_ID if "SRU" in s.upper() else None
        )
        print(f"[wowa_types] Scraped {len(df)} REITs (name/symbol/type) from wowa.ca")
        return df

    except Exception as e:
        print(f"[wowa_types] Live scrape failed ({e}) - returning fallback sample")
        fallback_rows = [
            ["SmartCentres REIT", "SRU.UN", "Retail"],
            ["RioCan REIT", "REI.UN", "Retail"],
            ["CT REIT", "CRT.UN", "Retail"],
            ["Choice Properties REIT", "CHP.UN", "Commercial / Residential"],
        ]
        df = pd.DataFrame(fallback_rows, columns=["reit_name", "symbol", "reit_type"])
        df["source"] = "wowa.ca_fallback"
        df["pulled_at"] = datetime.now().isoformat()
        df["company_id"] = df["symbol"].apply(
            lambda s: COMPANY_ID if "SRU" in s.upper() else None
        )
        return df


def get_current_peer_metrics(tickers=PEER_TICKERS):
    """
    Pulls CURRENT share price and dividend yield for each peer via yfinance,
    since the wowa.ca figures are stale. Returns a structured DataFrame -> MySQL.
    """
    rows = []
    for company_id, ticker in tickers.items():
        try:
            tkr = yf.Ticker(ticker)
            info = tkr.info
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            yield_pct = info.get("dividendYield")
            if price is None:
                raise ValueError(f"No current price returned for {ticker}")
            rows.append({
                "company_id": company_id,
                "symbol": ticker,
                "current_price": price,
                "dividend_yield": yield_pct,
                "source": "yfinance",
                "pulled_at": datetime.now().isoformat(),
            })
            print(f"[peer_metrics] {ticker}: price={price}, yield={yield_pct}")
        except Exception as e:
            print(f"[peer_metrics] Failed for {ticker} ({e}) - skipping")
            rows.append({
                "company_id": company_id,
                "symbol": ticker,
                "current_price": None,
                "dividend_yield": None,
                "source": "yfinance_fallback",
                "pulled_at": datetime.now().isoformat(),
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    types_df = get_reit_types()
    print(types_df)
    print()
    metrics_df = get_current_peer_metrics()
    print(metrics_df)