"""
BSMM-8730 — Smart Centres REIT Analysis
Script: MongoDB Insights Extraction
Author: Muhammad Ahmad
Role: Member C — MongoDB Analysis
Date: July 2026

What this script does:
- Connects to MongoDB Atlas
- Extracts key insights from all 4 collections:
    1. fundamentals     — financial metrics for investment analysis
    2. news_headlines   — sentiment and recent media coverage
    3. sedar_documents  — occupancy, NOI, interest rate risk commentary
    4. investor_documents — key financial highlights from press releases
- Saves results to analysis/outputs/ as CSV and text files
- Everything Eric needs to build the MongoDB charts
"""

import os
import re
import json
import certifi
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# ============================================================
# SETTINGS
# ============================================================

MONGO_URI = "mongodb+srv://usman:MongoFix2026@cluster0.ectjwst.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME   = "smartcentres"
OUTPUT_DIR = "analysis/outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# STEP 1 — Connect to MongoDB
# ============================================================

def connect_to_mongodb(uri):
    print("Connecting to MongoDB Atlas...")
    client = MongoClient(uri, tlsCAFile=certifi.where())
    db = client[DB_NAME]
    print(f"Connected! Using database: {DB_NAME}")
    print()
    return client, db


# ============================================================
# STEP 2 — Extract Fundamentals Insights
# ============================================================

def extract_fundamentals(db):
    """
    Extracts key financial metrics from the fundamentals collection.
    These are the headline numbers for the investment recommendation.
    """
    print("=" * 60)
    print("EXTRACTING: fundamentals")
    print("=" * 60)

    doc        = db["fundamentals"].find_one()
    fields     = doc.get("fundamentals", {})

    # Key metrics we care about for investment analysis
    metrics = {
        "company"                : fields.get("longName"),
        "ticker"                 : fields.get("symbol"),
        "sector"                 : fields.get("sector"),
        "industry"               : fields.get("industry"),
        "current_price_cad"      : fields.get("currentPrice"),
        "market_cap_cad"         : fields.get("marketCap"),
        "dividend_yield_pct"     : fields.get("dividendYield"),
        "dividend_rate_cad"      : fields.get("dividendRate"),
        "payout_ratio"           : round(fields.get("payoutRatio", 0) * 100, 2),
        "five_year_avg_yield_pct": fields.get("fiveYearAvgDividendYield"),
        "beta"                   : fields.get("beta"),
        "trailing_pe"            : fields.get("trailingPE"),
        "book_value"             : fields.get("bookValue"),
        "price_to_book"          : fields.get("priceToBook"),
        "total_debt_cad"         : fields.get("totalDebt"),
        "debt_to_equity"         : fields.get("debtToEquity"),
        "total_revenue_cad"      : fields.get("totalRevenue"),
        "ebitda_cad"             : fields.get("ebitda"),
        "operating_margin_pct"   : round(fields.get("operatingMargins", 0) * 100, 2),
        "profit_margin_pct"      : round(fields.get("profitMargins", 0) * 100, 2),
        "return_on_equity_pct"   : round(fields.get("returnOnEquity", 0) * 100, 2),
        "return_on_assets_pct"   : round(fields.get("returnOnAssets", 0) * 100, 2),
        "52_week_low"            : fields.get("fiftyTwoWeekLow"),
        "52_week_high"           : fields.get("fiftyTwoWeekHigh"),
        "52_week_change_pct"     : round(fields.get("52WeekChange", 0) * 100, 2),
        "analyst_target_price"   : fields.get("targetMeanPrice"),
        "analyst_opinions"       : fields.get("numberOfAnalystOpinions"),
        "recommendation"         : fields.get("recommendationKey"),
        "occupancy_pct"          : 97.6,   # From longBusinessSummary
        "total_assets_sqft"      : "35.5 million sq ft",
        "properties_count"       : 200,
    }

    print("Key metrics extracted:")
    for key, val in metrics.items():
        print(f"  {key}: {val}")

    # Save as CSV
    df = pd.DataFrame([metrics])
    df.to_csv(f"{OUTPUT_DIR}/fundamentals_metrics.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR}/fundamentals_metrics.csv")
    print()

    return metrics


# ============================================================
# STEP 3 — Extract News Headlines Insights
# ============================================================

def extract_news_insights(db):
    """
    Extracts and analyzes news headlines.
    Classifies each headline by sentiment and theme.
    """
    print("=" * 60)
    print("EXTRACTING: news_headlines")
    print("=" * 60)

    docs      = list(db["news_headlines"].find())
    headlines = [doc.get("headline", "") for doc in docs]

    print(f"Total headlines: {len(headlines)}")
    print()

    # Classify each headline by sentiment
    rows = []
    for doc in docs:
        headline = doc.get("headline", "")
        publisher = doc.get("publisher", "")

        # Simple sentiment classification
        positive_words = ["upgraded", "strong buy", "best", "momentum",
                         "growth", "strong", "highlights", "returns"]
        negative_words = ["too late", "risk", "concern", "drop",
                         "decline", "warning", "weak"]

        headline_lower = headline.lower()

        if any(word in headline_lower for word in positive_words):
            sentiment = "Positive"
        elif any(word in headline_lower for word in negative_words):
            sentiment = "Cautious"
        else:
            sentiment = "Neutral"

        # Classify theme
        if "valuation" in headline_lower:
            theme = "Valuation"
        elif "dividend" in headline_lower or "income" in headline_lower:
            theme = "Income/Dividend"
        elif "earnings" in headline_lower or "q4" in headline_lower or "q1" in headline_lower:
            theme = "Earnings"
        elif "buy" in headline_lower or "upgrade" in headline_lower:
            theme = "Analyst Rating"
        elif "governance" in headline_lower or "leadership" in headline_lower:
            theme = "Governance"
        elif "return" in headline_lower:
            theme = "Returns"
        else:
            theme = "General"

        rows.append({
            "headline" : headline,
            "publisher": publisher,
            "sentiment": sentiment,
            "theme"    : theme
        })
        print(f"  [{sentiment}] [{theme}] {headline[:80]}...")

    # Save as CSV
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTPUT_DIR}/news_sentiment.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR}/news_sentiment.csv")

    # Summary
    print()
    print("Sentiment Summary:")
    print(df["sentiment"].value_counts().to_string())
    print()
    print("Theme Summary:")
    print(df["theme"].value_counts().to_string())
    print()

    return df


# ============================================================
# STEP 4 — Extract SEDAR Documents Insights
# ============================================================

def extract_sedar_insights(db):
    """
    Extracts key passages from SEDAR MD&A documents.
    Looks for occupancy, NOI, interest rate risk, and debt mentions.
    """
    print("=" * 60)
    print("EXTRACTING: sedar_documents")
    print("=" * 60)

    docs = list(db["sedar_documents"].find())
    print(f"Total SEDAR documents: {len(docs)}")
    print()

    # Keywords to search for in the text
    search_terms = {
        "occupancy"     : ["occupancy", "occupied", "in-place"],
        "NOI"           : ["net operating income", "noi"],
        "interest_rate" : ["interest rate", "rate risk", "borrowing cost"],
        "debt"          : ["total debt", "mortgage", "debenture"],
        "dividend"      : ["distribution", "dividend per unit"],
        "development"   : ["development", "construction", "pipeline"],
    }

    rows = []
    for doc in docs:
        text     = doc.get("text", "")
        filename = doc.get("filename", "")
        year     = doc.get("document_year", "")

        print(f"Analyzing: {filename} (Year: {year})")

        for theme, keywords in search_terms.items():
            for keyword in keywords:
                # Find sentences containing the keyword
                sentences = re.split(r'(?<=[.!?])\s+', text)
                for sentence in sentences:
                    if keyword.lower() in sentence.lower() and len(sentence) > 50:
                        rows.append({
                            "document_year" : year,
                            "filename"      : filename,
                            "theme"         : theme,
                            "keyword"       : keyword,
                            "excerpt"       : sentence[:300].strip()
                        })
                        break  # One excerpt per keyword per doc

    # Save as CSV
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTPUT_DIR}/sedar_key_excerpts.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR}/sedar_key_excerpts.csv")
    print(f"Total excerpts extracted: {len(df)}")
    print()

    return df


# ============================================================
# STEP 5 — Extract Investor Documents Insights
# ============================================================

def extract_investor_insights(db):
    """
    Extracts key highlights from investor documents.
    Focuses on press releases, quarterly reports, and annual reports.
    """
    print("=" * 60)
    print("EXTRACTING: investor_documents")
    print("=" * 60)

    docs = list(db["investor_documents"].find())
    print(f"Total investor documents: {len(docs)}")
    print()

    # Keywords to search for
    search_terms = {
        "FFO"           : ["ffo", "funds from operations"],
        "occupancy"     : ["occupancy", "occupied"],
        "NOI"           : ["net operating income", "noi"],
        "distribution"  : ["distribution", "dividend"],
        "development"   : ["development", "construction"],
        "guidance"      : ["guidance", "outlook", "forecast"],
    }

    rows = []
    for doc in docs:
        text     = doc.get("text", "")
        filename = doc.get("filename", "")
        year     = doc.get("document_year", "")
        doc_type = doc.get("doc_type", "")

        print(f"Analyzing: {filename} ({doc_type}, {year})")

        for theme, keywords in search_terms.items():
            for keyword in keywords:
                sentences = re.split(r'(?<=[.!?])\s+', text)
                for sentence in sentences:
                    if keyword.lower() in sentence.lower() and len(sentence) > 50:
                        rows.append({
                            "document_year" : year,
                            "doc_type"      : doc_type,
                            "filename"      : filename,
                            "theme"         : theme,
                            "keyword"       : keyword,
                            "excerpt"       : sentence[:300].strip()
                        })
                        break

    # Save as CSV
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTPUT_DIR}/investor_doc_excerpts.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR}/investor_doc_excerpts.csv")
    print(f"Total excerpts extracted: {len(df)}")
    print()

    return df


# ============================================================
# STEP 6 — Save Full Summary Report
# ============================================================

def save_summary_report(metrics, news_df, sedar_df, investor_df):
    """
    Saves a clean text summary of all MongoDB insights.
    This is what goes directly to Amna for Section E of the report.
    """
    print("=" * 60)
    print("SAVING: MongoDB Insights Summary")
    print("=" * 60)

    summary = f"""
MONGODB INSIGHTS SUMMARY — SMART CENTRES REIT
Author: Muhammad Ahmad
Date: July 2026
Database: MongoDB Atlas — smartcentres

============================================================
1. COMPANY FUNDAMENTALS (from yfinance fundamentals collection)
============================================================

Company         : {metrics['company']}
Ticker          : {metrics['ticker']}
Sector          : {metrics['sector']}
Industry        : {metrics['industry']}

INVESTMENT METRICS:
  Current Price     : ${metrics['current_price_cad']} CAD
  Market Cap        : ${metrics['market_cap_cad']:,} CAD
  Dividend Yield    : {metrics['dividend_yield_pct']}%
  Dividend Rate     : ${metrics['dividend_rate_cad']} per unit
  Payout Ratio      : {metrics['payout_ratio']}%
  5-Year Avg Yield  : {metrics['five_year_avg_yield_pct']}%
  Beta              : {metrics['beta']} (market sensitivity)

VALUATION:
  Trailing P/E      : {metrics['trailing_pe']}
  Price to Book     : {metrics['price_to_book']}
  Book Value        : ${metrics['book_value']}
  52-Week Low       : ${metrics['52_week_low']}
  52-Week High      : ${metrics['52_week_high']}
  52-Week Change    : {metrics['52_week_change_pct']}%

FINANCIAL HEALTH:
  Total Debt        : ${metrics['total_debt_cad']:,} CAD
  Debt to Equity    : {metrics['debt_to_equity']}%
  Total Revenue     : ${metrics['total_revenue_cad']:,} CAD
  EBITDA            : ${metrics['ebitda_cad']:,} CAD
  Operating Margin  : {metrics['operating_margin_pct']}%
  Profit Margin     : {metrics['profit_margin_pct']}%
  Return on Equity  : {metrics['return_on_equity_pct']}%
  Return on Assets  : {metrics['return_on_assets_pct']}%

PORTFOLIO:
  Occupancy         : {metrics['occupancy_pct']}%
  Properties        : {metrics['properties_count']} locations
  Total Space       : {metrics['total_assets_sqft']}

ANALYST COVERAGE:
  Target Price      : ${metrics['analyst_target_price']} CAD
  Analyst Opinions  : {metrics['analyst_opinions']}
  Recommendation    : {metrics['recommendation']}

============================================================
2. NEWS SENTIMENT (from yfinance news_headlines collection)
============================================================

Total Headlines: {len(news_df)}

Sentiment Breakdown:
{news_df['sentiment'].value_counts().to_string()}

Theme Breakdown:
{news_df['theme'].value_counts().to_string()}

Key Headlines:
"""

    for _, row in news_df.iterrows():
        summary += f"\n  [{row['sentiment']}] {row['headline']}"

    summary += f"""

============================================================
3. SEDAR DOCUMENTS KEY EXCERPTS
============================================================

Total excerpts extracted: {len(sedar_df)}
Documents analyzed: 3 (Annual MD&A 2024, 2025, Q1 2026)

Themes found: {', '.join(sedar_df['theme'].unique()) if not sedar_df.empty else 'None'}

"""

    if not sedar_df.empty:
        for theme in sedar_df['theme'].unique():
            theme_rows = sedar_df[sedar_df['theme'] == theme]
            summary += f"\n{theme.upper()}:\n"
            for _, row in theme_rows.head(2).iterrows():
                summary += f"  [{row['document_year']}] {row['excerpt'][:200]}...\n"

    summary += f"""
============================================================
4. INVESTOR DOCUMENTS KEY EXCERPTS
============================================================

Total excerpts extracted: {len(investor_df)}
Documents analyzed: 10 (Press releases, AIF, Annual report, Q1 docs)

Themes found: {', '.join(investor_df['theme'].unique()) if not investor_df.empty else 'None'}

"""

    if not investor_df.empty:
        for theme in investor_df['theme'].unique():
            theme_rows = investor_df[investor_df['theme'] == theme]
            summary += f"\n{theme.upper()}:\n"
            for _, row in theme_rows.head(2).iterrows():
                summary += f"  [{row['document_year']}] [{row['doc_type']}] {row['excerpt'][:200]}...\n"

    summary += """
============================================================
END OF MONGODB INSIGHTS SUMMARY
============================================================
"""

    # Save summary as text file
    with open(f"{OUTPUT_DIR}/mongodb_insights_summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)

    print(summary)
    print(f"Saved: {OUTPUT_DIR}/mongodb_insights_summary.txt")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("BSMM-8730 — MongoDB Insights Extraction")
    print("Author : Muhammad Ahmad")
    print("Date   : July 2026")
    print("=" * 60)
    print()

    client = None
    try:
        client, db = connect_to_mongodb(MONGO_URI)

        # Extract insights from all 4 collections
        metrics     = extract_fundamentals(db)
        news_df     = extract_news_insights(db)
        sedar_df    = extract_sedar_insights(db)
        investor_df = extract_investor_insights(db)

        # Save full summary report
        save_summary_report(metrics, news_df, sedar_df, investor_df)

        print()
        print("=" * 60)
        print("All MongoDB insights extracted successfully!")
        print(f"Files saved in: {OUTPUT_DIR}/")
        print("  - fundamentals_metrics.csv")
        print("  - news_sentiment.csv")
        print("  - sedar_key_excerpts.csv")
        print("  - investor_doc_excerpts.csv")
        print("  - mongodb_insights_summary.txt")
        print("=" * 60)

    except PyMongoError as e:
        print(f"MongoDB connection error: {e}")
        print("Check your internet connection and try again.")

    finally:
        if client:
            client.close()
            print()
            print("MongoDB connection closed.")
