"""
generate_sample_data.py
========================
Creates a synthetic 2-year DAILY dataset for the 10 required tickers, with
the exact schema the pipeline expects:

    date,volume,open,high,low,close,adjclose,ticker

This is ONLY here so the project is runnable end-to-end out of the box.
Drop your own real daily CSV into data/ and point pipeline.py at it instead.
"""

import numpy as np
import pandas as pd

TICKERS = ["AAPL", "AMD", "AMZN", "AVGO", "CSCO", "MSFT", "NFLX", "PEP", "TMUS", "TSLA"]
START, END = "2023-10-01", "2025-09-30"  # exactly 24 months of business days
OUT_PATH = "data/test_sample_daily_prices.csv"


def generate(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(START, END)
    rows = []

    for ticker in TICKERS:
        price = rng.uniform(50, 400)
        for d in dates:
            price = max(price * (1 + rng.normal(0, 0.015)), 1.0)
            o = price * (1 + rng.normal(0, 0.003))
            h = max(o, price) * (1 + abs(rng.normal(0, 0.005)))
            l = min(o, price) * (1 - abs(rng.normal(0, 0.005)))
            v = int(rng.uniform(1e6, 5e7))
            rows.append([d, v, round(o, 2), round(h, 2), round(l, 2), round(price, 2), round(price, 2), ticker])

    return pd.DataFrame(rows, columns=["date", "volume", "open", "high", "low", "close", "adjclose", "ticker"])


if __name__ == "__main__":
    df = generate()
    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(df)} rows ({df['ticker'].nunique()} tickers) to {OUT_PATH}")
