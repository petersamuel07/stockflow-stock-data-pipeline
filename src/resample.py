"""
resample.py
===========
Daily -> monthly OHLC resampling. This is the "Calculation Logic" for
aggregation only; technical indicators live in indicators.py.
"""

from __future__ import annotations

import pandas as pd


def resample_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resample daily rows to monthly OHLC, per ticker.

    Open  -> price on the FIRST trading day of the month (a snapshot, not an average)
    Close -> price on the LAST trading day of the month  (a snapshot, not an average)
    High  -> max of the daily highs during the month
    Low   -> min of the daily lows during the month
    Volume-> summed over the month (kept as useful context; see README assumptions)
    """
    work = df.copy()
    work["month"] = work["date"].dt.to_period("M")
    work = work.sort_values(["ticker", "month", "date"])

    grouped = work.groupby(["ticker", "month"], sort=True)

    monthly = grouped.agg(
        open=("open", "first"),
        close=("close", "last"),
        high=("high", "max"),
        low=("low", "min"),
        volume=("volume", "sum"),
    ).reset_index()

    monthly["date"] = monthly["month"].dt.to_timestamp()
    monthly = monthly.sort_values(["ticker", "date"]).reset_index(drop=True)
    return monthly[["ticker", "month", "date", "open", "high", "low", "close", "volume"]]
