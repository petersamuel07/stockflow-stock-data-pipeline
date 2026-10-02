"""
pipeline.py
===========
Orchestration layer + CLI entry point. Wires together:

    io_utils.load_data
      -> resample.resample_to_monthly
      -> indicators.calculate_indicators
      -> io_utils.partition_and_write

Usage:
    python pipeline.py --input ../data/test_sample_daily_prices.csv(for testing) --outdir ../output
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from io_utils import load_data, partition_and_write
from resample import resample_to_monthly
from indicators import calculate_indicators


def run_pipeline(input_path: str | Path, outdir: str | Path) -> list[Path]:
    """End-to-end pipeline: load -> resample -> enrich -> partition & write."""
    daily = load_data(input_path)
    monthly = resample_to_monthly(daily)
    enriched = calculate_indicators(monthly)
    return partition_and_write(enriched, outdir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily-to-monthly stock data pipeline")
    parser.add_argument("--input", required=True, help="Path to the raw daily CSV")
    parser.add_argument("--outdir", default="../output", help="Directory for result_{SYMBOL}.csv files")
    args = parser.parse_args()

    paths = run_pipeline(args.input, args.outdir)
    print(f"Wrote {len(paths)} files to {os.path.abspath(args.outdir)}:")
    for p in paths:
        print(f"  - {p.name}")


if __name__ == "__main__":
    main()
