"""
indicators.py
=============
Technical indicator "Calculation Logic", kept separate from aggregation
(resample.py) and file I/O (io_utils.py). Every function is a plain
pandas/numpy implementation - no 3rd-party technical-analysis library.

EMA implementation note
------------------------
Per the assignment references (Investopedia, Groww) the EMA is NOT the
"adjust=False" exponential weighting pandas' .ewm() gives you out of the
box - it is the classic recursive formula, seeded with a plain SMA:

    Multiplier = 2 / (N + 1)
    EMA[0]     = SMA(first N closes)                      <- seed
    EMA[i]     = (Close[i] - EMA[i-1]) * Multiplier + EMA[i-1]

`calculate_ema` below implements exactly that (vectorized SMA seed +
a short recursive fill-in, since EMA is inherently sequential/stateful
and cannot be fully vectorized without re-deriving the closed-form
geometric-series expansion).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import (
    SMA_WINDOWS,
    EMA_WINDOWS,
    DONCHIAN_WINDOW,
    BOLLINGER_WINDOW,
    BOLLINGER_K,
    ZSCORE_WINDOW,
)


def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average: sum of last N closes / N (pandas rolling mean)."""
    return series.rolling(window=window, min_periods=window).mean()


def calculate_ema(series: pd.Series, window: int) -> pd.Series:
    """
    Exponential Moving Average, SMA-seeded, per the Investopedia / Groww
    recursive definition (see module docstring).
    """
    multiplier = 2 / (window + 1)
    sma_seed = calculate_sma(series, window)

    ema = pd.Series(np.nan, index=series.index, dtype=float)
    seed_pos = window - 1
    if len(series) <= seed_pos or pd.isna(sma_seed.iloc[seed_pos]):
        return ema

    ema.iloc[seed_pos] = sma_seed.iloc[seed_pos]
    prev = ema.iloc[seed_pos]
    for i in range(seed_pos + 1, len(series)):
        prev = (series.iloc[i] - prev) * multiplier + prev
        ema.iloc[i] = prev

    return ema


def calculate_donchian(high: pd.Series, low: pd.Series, window: int) -> tuple[pd.Series, pd.Series]:
    """Donchian Channel: rolling max of highs / rolling min of lows."""
    upper = high.rolling(window=window, min_periods=window).max()
    lower = low.rolling(window=window, min_periods=window).min()
    return upper, lower


def calculate_bollinger(close: pd.Series, window: int, k: float) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands: mid = rolling mean, bands = mid +/- k * rolling std."""
    mid = close.rolling(window=window, min_periods=window).mean()
    sd = close.rolling(window=window, min_periods=window).std()
    return mid, mid + k * sd, mid - k * sd


def calculate_zscore(close: pd.Series, window: int) -> pd.Series:
    """Rolling Z-score of the close price: (close - rolling mean) / rolling std."""
    roll_mean = close.rolling(window=window, min_periods=window).mean()
    roll_std = close.rolling(window=window, min_periods=window).std()
    return (close - roll_mean) / roll_std


def enrich_ticker(group: pd.DataFrame) -> pd.DataFrame:
    """Add every indicator column to a single ticker's monthly history."""
    g = group.sort_values("date").copy()
    close, high, low = g["close"], g["high"], g["low"]

    for w in SMA_WINDOWS:
        g[f"SMA_{w}"] = calculate_sma(close, w)
    for w in EMA_WINDOWS:
        g[f"EMA_{w}"] = calculate_ema(close, w)

    donch_upper, donch_lower = calculate_donchian(high, low, DONCHIAN_WINDOW)
    g[f"Donchian_Upper_{DONCHIAN_WINDOW}"] = donch_upper
    g[f"Donchian_Lower_{DONCHIAN_WINDOW}"] = donch_lower

    bb_mid, bb_upper, bb_lower = calculate_bollinger(close, BOLLINGER_WINDOW, BOLLINGER_K)
    g[f"BB_Mid_{BOLLINGER_WINDOW}"] = bb_mid
    g[f"BB_Upper_{BOLLINGER_WINDOW}"] = bb_upper
    g[f"BB_Lower_{BOLLINGER_WINDOW}"] = bb_lower

    g[f"Zscore_{ZSCORE_WINDOW}"] = calculate_zscore(close, ZSCORE_WINDOW)
    return g


def calculate_indicators(monthly: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicator columns to the monthly dataset.
    Every indicator is computed independently per ticker so one symbol's
    history never leaks into another's rolling window.
    """
    monthly = monthly.sort_values(["ticker", "date"]).copy()

    enriched_groups = []
    for ticker, group in monthly.groupby("ticker", sort=True):
        g = enrich_ticker(group)
        g["ticker"] = ticker  # re-attach explicitly (defensive, see README)
        enriched_groups.append(g)

    return pd.concat(enriched_groups, ignore_index=True)
