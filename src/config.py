"""
config.py
=========
Single source of truth for every tunable parameter in the pipeline.
Change a window/multiplier here rather than hunting through the code.

See README.md -> "Assumptions" for why these specific values were chosen.
"""

REQUIRED_COLUMNS = ["date", "volume", "open", "high", "low", "close", "adjclose", "ticker"]

# Moving average windows, expressed in MONTHS (the data is already monthly by
# the time these are applied).
SMA_WINDOWS = (10, 20)
EMA_WINDOWS = (10, 20)

# Donchian Channel / Bollinger Band / Z-score lookback window (months).
DONCHIAN_WINDOW = 20
BOLLINGER_WINDOW = 20
BOLLINGER_K = 2          # standard-deviation multiplier for the bands
ZSCORE_WINDOW = 20

OUTPUT_FILENAME_TEMPLATE = "result_{ticker}.csv"
