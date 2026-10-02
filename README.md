# STOCKFLOW Daily → Monthly Stock Data Pipeline

A modular Pandas-based pipeline that converts daily OHLCV stock data into monthly summaries, adds technical indicators, and writes one CSV per ticker.

This project is designed to work with any valid daily stock dataset that follows the expected schema. For testing and local validation, a generated synthetic dataset is included. For the actual assignment, the required input is the provided dataset in the data folder.

## Project structure

```
.
├── README.md
├── requirements.txt
├── generate_sample_data.py      # creates a synthetic 2-year daily dataset (demo/testing only)
├── data/
│   └── sample_daily_prices.csv  # synthetic input used for the included output/
├── output/
│   └── result_{SYMBOL}.csv      # pre-generated sample output (10 files, 24 rows each)
└── src/
    ├── config.py                # all tunable constants (windows, k, filenames)
    ├── io_utils.py              # CSV loading + partitioned file writing
    ├── resample.py              # daily -> monthly OHLC aggregation logic
    ├── indicators.py            # SMA / EMA / Donchian / Bollinger / Z-score math
    └── pipeline.py              # orchestrates the above + CLI entry point
```

Each module has a single responsibility, per the assignment's "Code
Structure" requirement:

- **`resample.py`** — only the OHLC aggregation logic (the "what the monthly
  bar looks like" question).
- **`indicators.py`** — only the technical-indicator math. Pure pandas/numpy,
  no 3rd-party TA library.
- **`io_utils.py`** — only reading the raw file and writing the partitioned
  output files.
- **`pipeline.py`** — wires the three together and exposes the CLI.

## How to run

```bash
pip install -r requirements.txt

# Optional: regenerate the synthetic test data
python generate_sample_data.py

# Run against the synthetic data
python src/pipeline.py --input data/test_sample_daily_prices.csv --outdir output

# Run against the assignment dataset
python src/pipeline.py --input data/tt_dataset.csv --outdir output
```

This produces `result_AAPL.csv`, `result_AMD.csv`, … `result_TSLA.csv` in
`output/`, each with exactly 24 rows (one per month).

To run against your own real dataset, just point `--input` at it — the only
requirement is the column schema below.

## Input schema

```
date,volume,open,high,low,close,adjclose,ticker
```

## Output columns

`ticker, date, open, high, low, close, volume, SMA_10, SMA_20, EMA_10,
EMA_20, Donchian_Upper_20, Donchian_Lower_20, BB_Mid_20, BB_Upper_20,
BB_Lower_20, Zscore_20`

The first 9/19 rows of any 10/20-period indicator are `NaN` by definition —
there isn't enough monthly history yet to fill the window. This is expected,
not a bug.

## Formulas implemented

**Simple Moving Average (SMA)**
```
SMA(N) = sum(last N monthly closes) / N
```
Implemented as `close.rolling(window=N).mean()`.

**Exponential Moving Average (EMA)** — implemented per the assignment's
reference formula (Investopedia / Groww), *not* pandas' default
`.ewm(adjust=False)` weighting:
```
Multiplier = 2 / (N + 1)
EMA[seed]  = SMA(first N closes)                      # seed value
EMA[i]     = (Close[i] - EMA[i-1]) * Multiplier + EMA[i-1]
```
This is inherently recursive/stateful, so `calculate_ema()` computes the SMA
seed vectorized and then fills forward with a short loop — the rest of the
pipeline (resampling, SMA, Donchian, Bollinger, Z-score) is fully vectorized.

**Donchian Channels**
```
Upper = high.rolling(N).max()
Lower = low.rolling(N).min()
```

**Bollinger Bands**
```
mid   = close.rolling(N).mean()
sd    = close.rolling(N).std()
upper = mid + k * sd
lower = mid - k * sd
```

**Z-score (volatility indicator)**
```
z = (close - close.rolling(N).mean()) / close.rolling(N).std()
```

## Assumptions

The assignment left a few parameters and edge cases unspecified. Practical
choices made here, all centralized in `src/config.py` so they're easy to
change:

1. **Lookback windows.** SMA/EMA are required at both 10 and 20 periods.
   Donchian Channels, Bollinger Bands, and the Z-score weren't given an
   explicit window in the spec, so all three default to **20 months** (the
   longer of the two given windows). Change `DONCHIAN_WINDOW`,
   `BOLLINGER_WINDOW`, `ZSCORE_WINDOW` in `config.py` if a different period
   is wanted.
2. **Bollinger multiplier.** `k = 2`, the conventional default.
3. **Indicator basis.** As stated in the spec, every indicator is calculated
   on the **monthly closing price**, except the Donchian Channel, which by
   definition needs the monthly high/low rather than the close.
4. **Per-ticker isolation.** All rolling/EMA calculations are computed
   independently per ticker (grouped first), so one symbol's rolling window
   never pulls in another symbol's data even though the master file is one
   CSV.
5. **Monthly volume.** Not required by the spec, but a monthly `volume`
   column (sum of daily volumes) is included as a natural byproduct of the
   groupby and left in since it's harmless, useful context, and easy to
   drop from `export_cols` in `io_utils.py` if an exact column match to the
   spec is required.
6. **"Exactly 24 rows" assumption.** This holds when the input covers
   exactly a 2-year span with at least one trading day in every calendar
   month — true for the provided `tt_dataset.csv`. If a different dataset
   has a gapped or partial month, that month will simply be absent from the
   output rather than silently fabricated.

## References

- https://www.investopedia.com/terms/e/ema.asp
- https://groww.in/p/exponential-moving-average
