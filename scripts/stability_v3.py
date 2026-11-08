"""Descriptive parameter-stability and trade-concentration diagnostics.

This is exploratory only. It does not modify any pre-registered rule or verdict.
All lookbacks are evaluated on the same common bar range to avoid warm-up bias.
Primary comparison is gross returns; net returns use the repository's fixed cost
convention and are supplemental. Trade concentration is a descriptive heuristic.
Run from the repository root:
    python scripts/stability_v3.py
"""
import glob
import hashlib
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.momentum import COST_PER_SIDE, positions  # noqa: E402

LOOKBACKS = [21, 42, 63, 84]
BARS_PER_YEAR = 6 * 365
N_WINDOWS = 6
TOP_K_TRADES = 5
RAW = os.path.join(ROOT, "data", "raw")
CHECKSUMS = os.path.join(ROOT, "data", "CHECKSUMS.txt")
OUT_DIR = os.path.join(ROOT, "results", "diagnostics")


def verify_checksums():
    expected = {}
    with open(CHECKSUMS, encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            digest, name = line.split("  ", 1)
            expected[os.path.basename(name)] = digest
    missing, bad = [], []
    for name, digest in expected.items():
        path = os.path.join(RAW, name)
        if not os.path.isfile(path):
            missing.append(name)
            continue
        with open(path, "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()
        if actual != digest:
            bad.append(name)
    if missing or bad:
        raise RuntimeError(f"Checksum verification failed; missing={missing}; mismatched={bad}")
    return len(expected)


def load_close(symbol):
    files = sorted(glob.glob(os.path.join(RAW, f"{symbol}-4h-*.csv")))
    if not files:
        raise FileNotFoundError(f"No raw monthly files found for {symbol} in {RAW}")
    frames = [pd.read_csv(path, header=None, usecols=[0, 4]) for path in files]
    df = pd.concat(frames, ignore_index=True)
    df.columns = ["open_time", "close"]
    df["open_time"] = pd.to_numeric(df["open_time"], errors="raise")
    df["close"] = pd.to_numeric(df["close"], errors="raise")
    df = df.drop_duplicates("open_time").sort_values("open_time")
    return df.set_index("open_time")["close"].astype(float)


def sharpe(returns):
    r = returns.dropna()
    sd = r.std(ddof=1)
    if len(r) < 2 or not np.isfinite(sd) or sd <= 0:
        return np.nan
    return float(r.mean() / sd * np.sqrt(BARS_PER_YEAR))


def trade_episode_returns(position, bar_returns):
    """Compound gross returns for each contiguous long episode."""
    active = position.fillna(0).astype(int).eq(1)
    starts = active & ~active.shift(1, fill_value=False)
    groups = starts.cumsum()
    episode_returns = []
    for group_id in groups[active].unique():
        mask = active & groups.eq(group_id)
        r = bar_returns.loc[mask].dropna()
        if not r.empty:
            episode_returns.append(float((1.0 + r).prod() - 1.0))
    return episode_returns


def evaluate(close, lookback, common_start):
    signal_position = positions(close, lookback).fillna(0.0)
    bar_returns = close.pct_change()
    gross = signal_position * bar_returns
    turnover = signal_position.diff().abs()
    turnover.iloc[0] = abs(signal_position.iloc[0])
    net = gross - COST_PER_SIDE * turnover.fillna(0.0)

    # All lookbacks use the exact same timestamps for a fair comparison.
    gross_eval = gross.loc[common_start:].dropna()
    net_eval = net.loc[common_start:].reindex(gross_eval.index)
    if len(gross_eval) < N_WINDOWS:
        raise ValueError("Not enough common evaluation bars to form six windows.")

    window_ids = np.array_split(np.arange(len(gross_eval)), N_WINDOWS)
    gross_windows, net_windows = [], []
    for ids in window_ids:
        gross_seg = gross_eval.iloc[ids]
        net_seg = net_eval.iloc[ids]
        gross_windows.append(float((1 + gross_seg).prod() - 1))
        net_windows.append(float((1 + net_seg).prod() - 1))

    episodes = trade_episode_returns(signal_position.loc[common_start:], bar_returns.loc[common_start:])
    positive_episode_sum = sum(x for x in episodes if x > 0)
    top_positive = sorted((x for x in episodes if x > 0), reverse=True)[:TOP_K_TRADES]
    concentration = (
        sum(top_positive) / positive_episode_sum * 100
        if positive_episode_sum > 0 else np.nan
    )
    return {
        "lookback": lookback,
        "bars_evaluated_common_range": len(gross_eval),
        "gross_total_return_pct": 100 * float((1 + gross_eval).prod() - 1),
        "gross_sharpe": sharpe(gross_eval),
        "net_total_return_pct": 100 * float((1 + net_eval).prod() - 1),
        "net_sharpe": sharpe(net_eval),
        "gross_positive_windows": sum(x > 0 for x in gross_windows),
        "gross_window_returns_pct": ";".join(f"{100*x:.2f}" for x in gross_windows),
        "net_positive_windows": sum(x > 0 for x in net_windows),
        "net_window_returns_pct": ";".join(f"{100*x:.2f}" for x in net_windows),
        "long_episodes": len(episodes),
        "positive_long_episodes": sum(x > 0 for x in episodes),
        "top5_share_of_positive_episode_returns_pct": concentration,
    }


def main():
    n_checksums = verify_checksums()
    rows = []
    for symbol in ("BTCUSDT", "ETHUSDT"):
        close = load_close(symbol)
        # First common bar where the 84-bar lookback and one-bar position lag
        # are both warmed up. Same timestamps are then used for all lookbacks.
        common_start = close.index[85]
        for lookback in LOOKBACKS:
            row = evaluate(close, lookback, common_start)
            row["symbol"] = symbol
            row["common_start_utc_ms"] = int(common_start)
            row["common_start_utc"] = pd.to_datetime(common_start, unit="ms", utc=True).isoformat()
            row["checksum_files_verified"] = n_checksums
            rows.append(row)

    result = pd.DataFrame(rows)
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "stability_v3_parameter_sensitivity.csv")
    result.to_csv(out_path, index=False, float_format="%.6f")
    print("Exploratory diagnostic only — no strategy acceptance decision.")
    print(result.to_string(index=False))
    print(f"\nSaved: {out_path}")
    for symbol in ("BTCUSDT", "ETHUSDT"):
        subset = result[result["symbol"] == symbol].set_index("lookback")
        peak = subset["gross_sharpe"].idxmax()
        peak_sharpe = subset.loc[peak, "gross_sharpe"]
        neighbours = [lb for lb in LOOKBACKS if lb != peak]
        retains = [
            subset.loc[lb, "gross_sharpe"] >= 0.75 * peak_sharpe
            if np.isfinite(peak_sharpe) and peak_sharpe > 0 else False
            for lb in neighbours
        ]
        print(
            f"{symbol}: highest gross Sharpe at lookback={peak}; "
            f"all other tested lookbacks retain >=75% of peak Sharpe: {all(retains)}. "
            "Heuristic only; lookbacks are not independent tests."
        )


if __name__ == "__main__":
    main()
