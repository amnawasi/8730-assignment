"""
analysis/make_charts.py
BSMM-8730 SmartCentres REIT - Track A visualizations.

Reads the CSVs Ahmad exported into analysis/outputs/ and produces
business-ready PNG charts (titled + labelled) back into the same folder.

Run from the repo root:  python analysis/make_charts.py
Dependencies:            pip install pandas matplotlib
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

OUT = Path("analysis/outputs")

plt.rcParams.update({
    "figure.figsize": (9, 5),
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.grid": True,
    "grid.alpha": 0.3,
})

BLUE, ORANGE, GREEN = "#1f5fa8", "#e07b39", "#2e8b57"


def save(fig, name):
    """Tidy layout and write a PNG."""
    fig.tight_layout()
    path = OUT / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {path}")


# 1. Price history - full timeline (line)
def chart_price_history():
    df = pd.read_csv(OUT / "price_history.csv", parse_dates=["date"])
    fig, ax = plt.subplots()
    ax.plot(df["date"], df["close"], color=BLUE, linewidth=1)
    ax.set_title("SmartCentres (SRU-UN.TO) Unit Price, 2020-2026")
    ax.set_xlabel("Date")
    ax.set_ylabel("Closing price (CAD)")
    save(fig, "chart_price_history.png")


# 2. Price vs interest rate (dual axis, yearly)
def chart_price_vs_rate():
    df = pd.read_csv(OUT / "price_vs_rate_yearly.csv")
    fig, ax1 = plt.subplots()
    ax1.bar(df["year"], df["avg_stock_price"], color=BLUE, alpha=0.7, label="Avg unit price")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Avg unit price (CAD)", color=BLUE)
    ax1.tick_params(axis="y", labelcolor=BLUE)

    ax2 = ax1.twinx()
    ax2.plot(df["year"], df["avg_interest_rate"], color=ORANGE, marker="o", linewidth=2, label="Avg overnight rate")
    ax2.set_ylabel("Avg overnight rate (%)", color=ORANGE)
    ax2.tick_params(axis="y", labelcolor=ORANGE)
    ax2.grid(False)

    ax1.set_title("Unit Price vs. Interest Rate by Year")
    save(fig, "chart_price_vs_rate.png")


# 3. Dividend yield vs peers (bar) - the recommendation chart
def chart_peer_yield():
    df = pd.read_csv(OUT / "peer_yield_comparison.csv").sort_values("dividend_yield_pct", ascending=False)
    df["dividend_yield_pct"] = df["dividend_yield_pct"] / 100
    colors = [ORANGE if "SRU" in str(s).upper() else BLUE for s in df["symbol"]]
    fig, ax = plt.subplots()
    ax.bar(df["symbol"], df["dividend_yield_pct"], color=colors)
    ax.set_title("Dividend Yield: SmartCentres vs. Peer REITs")
    ax.set_xlabel("REIT")
    ax.set_ylabel("Dividend yield (%)")
    for i, v in enumerate(df["dividend_yield_pct"]):
        ax.text(i, v, f"{v:.2f}%", ha="center", va="bottom", fontsize=9)
    save(fig, "chart_peer_yield.png")


# 4. Annual returns by year (bar, green up / red down)
def chart_annual_returns():
    df = pd.read_csv(OUT / "annual_returns.csv")
    colors = [GREEN if v >= 0 else "#c0392b" for v in df["annual_return_pct"]]
    fig, ax = plt.subplots()
    ax.bar(df["year"].astype(str), df["annual_return_pct"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("SmartCentres Annual Return by Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual return (%)")
    save(fig, "chart_annual_returns.png")


# 5. Era comparison (bar)
def chart_era_comparison():
    df = pd.read_csv(OUT / "era_comparison.csv")
    fig, ax = plt.subplots()
    ax.bar(df["market_era"], df["avg_stock_price"], color=BLUE)
    ax.set_title("Average Unit Price by Market Era")
    ax.set_xlabel("Market era")
    ax.set_ylabel("Avg unit price (CAD)")
    save(fig, "chart_era_comparison.png")


# 6. Rate environment vs price (bar)
def chart_rate_environment():
    df = pd.read_csv(OUT / "price_by_rate_environment.csv")
    fig, ax = plt.subplots()
    ax.bar(df["rate_environment"], df["avg_stock_price"], color=BLUE)
    ax.set_title("Average Unit Price by Interest-Rate Environment")
    ax.set_xlabel("Rate environment")
    ax.set_ylabel("Avg unit price (CAD)")
    save(fig, "chart_rate_environment.png")


# 7. Inflation vs price (dual-axis line)
def chart_inflation_vs_price():
    df = pd.read_csv(OUT / "inflation_vs_price.csv")
    fig, ax1 = plt.subplots()
    ax1.plot(df["year"], df["avg_stock_price"], color=BLUE, marker="o", label="Avg unit price")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Avg unit price (CAD)", color=BLUE)
    ax1.tick_params(axis="y", labelcolor=BLUE)

    ax2 = ax1.twinx()
    ax2.plot(df["year"], df["avg_cpi"], color=ORANGE, marker="s", label="Avg CPI")
    ax2.set_ylabel("Avg CPI", color=ORANGE)
    ax2.tick_params(axis="y", labelcolor=ORANGE)
    ax2.grid(False)

    ax1.set_title("Unit Price vs. Inflation (CPI) by Year")
    save(fig, "chart_inflation_vs_price.png")


# 8. News coverage themes (pie) - descriptive tone only, not predictive
def chart_news_sentiment():
    df = pd.read_csv(OUT / "news_sentiment.csv")
    counts = df["sentiment"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts, labels=counts.index, autopct="%1.0f%%", startangle=90,
           colors=[GREEN, "#95a5a6", "#c0392b"][:len(counts)])
    ax.set_title("Tone of Recent News Coverage")
    save(fig, "chart_news_sentiment.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("Building charts...")
    chart_price_history()
    chart_price_vs_rate()
    chart_peer_yield()
    chart_annual_returns()
    chart_era_comparison()
    chart_rate_environment()
    chart_inflation_vs_price()
    chart_news_sentiment()
    print("Done - 8 PNG charts written to analysis/outputs/")


if __name__ == "__main__":
    main()