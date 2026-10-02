"""
io_utils.py
===========
All file-system interaction lives here: reading the raw daily CSV and
writing the final per-ticker result files. Keeping this separate from the
calculation logic means the math can be unit-tested without touching disk.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import REQUIRED_COLUMNS, OUTPUT_FILENAME_TEMPLATE


def load_data(path: str | Path) -> pd.DataFrame:
    """Read the raw daily CSV and perform basic validation / typing."""
    df = pd.read_csv(path)

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {missing}")

    df["date"] = pd.to_datetime(df["date"])
    numeric_cols = ["volume", "open", "high", "low", "close", "adjclose"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


def partition_and_write(enriched: pd.DataFrame, outdir: str | Path) -> list[Path]:
    """Split the enriched monthly dataset into one CSV per ticker."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    export_cols = [c for c in enriched.columns if c != "month"]
    written_paths: list[Path] = []

    for ticker, group in enriched.groupby("ticker", sort=True):
        out_path = outdir / OUTPUT_FILENAME_TEMPLATE.format(ticker=ticker)
        group[export_cols].sort_values("date").to_csv(out_path, index=False)
        written_paths.append(out_path)

    return written_paths
