"""Time-series momentum signal and net-return accounting.

prereg-v1: LOOKBACK = 6 bars (default here, unchanged).
prereg-v2: lookback = 42 bars, passed explicitly by the v2 runner.

Rules:
- signal_t = 1 if close_t / close_(t-L) - 1 > 0 else 0 (long-only)
- position_t = signal_(t-1)  (decided at close of t-1, held over bar t)
- net_t = position_t * bar_return_t - COST_PER_SIDE * |position_t - position_(t-1)|
"""

import numpy as np
import pandas as pd

LOOKBACK = 6  # prereg-v1
COST_PER_SIDE = 0.0015  # 0.10% fee + 0.05% slippage


def signal(close: pd.Series, lookback: int = LOOKBACK) -> pd.Series:
    """Long-only signal using closes up to and including bar t."""
    past_return = close / close.shift(lookback) - 1.0
    return (past_return > 0).astype(float).where(past_return.notna())


def positions(close: pd.Series, lookback: int = LOOKBACK) -> pd.Series:
    """Position held over bar t, decided at close of bar t-1."""
    return signal(close, lookback).shift(1)


def net_returns(close: pd.Series, lookback: int = LOOKBACK) -> pd.Series:
    bar_return = close.pct_change()
    pos = positions(close, lookback)
    turnover = pos.diff().abs().fillna(pos.abs())
    return pos * bar_return - COST_PER_SIDE * turnover
