"""Run the pre-registered backtest (prereg-v1) on frozen BTC and ETH 4h data.

Rules are imported unchanged from src/momentum.py. Nothing here tunes parameters.
Writes results/prereg-v2.md. Run from the repository root.
"""

import glob
import hashlib
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.momentum import COST_PER_SIDE, net_returns  # noqa: E402

RUN_LOOKBACK = 42  # prereg-v2

BARS_PER_YEAR = 6 * 365  # 4h bars
N_WINDOWS = 6
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "results", "prereg-v2.md")


def verify_checksums():
    expected = {}
    with open(os.path.join(ROOT, "data", "CHECKSUMS.txt"), encoding="utf-8-sig") as fh:
        for line in fh:
            digest, name = line.strip().split("  ", 1)
            expected[os.path.basename(name)] = digest
    bad = []
    for name, digest in expected.items():
        with open(os.path.join(RAW, name), "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()
        if actual != digest:
            bad.append(name)
    return len(expected), bad


def load_close(symbol):
    files = sorted(glob.glob(os.path.join(RAW, f"{symbol}-4h-*.csv")))
    frames = [pd.read_csv(f, header=None, usecols=[0, 4]) for f in files]
    df = pd.concat(frames, ignore_index=True)
    df.columns = ["open_time", "close"]
    df = df.drop_duplicates("open_time").sort_values("open_time")
    return df["close"].astype(float).reset_index(drop=True), len(files), len(df)


def sharpe(r):
    r = r.dropna()
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(BARS_PER_YEAR)) if sd > 0 else float("nan")


def buy_and_hold(close):
    r = close.pct_change().dropna()
    r.iloc[0] -= COST_PER_SIDE  # entry
    r.iloc[-1] -= COST_PER_SIDE  # exit
    return r


def evaluate(symbol):
    close, n_files, n_rows = load_close(symbol)
    net = net_returns(close, RUN_LOOKBACK).dropna()
    bh = buy_and_hold(close).reindex(net.index).dropna()
    idx = np.array_split(np.arange(len(net)), N_WINDOWS)
    windows = []
    for k, w in enumerate(idx, start=1):
        seg = net.iloc[w]
        total = float((1 + seg).prod() - 1)
        windows.append((k, seg.index[0], seg.index[-1], total))
    positives = sum(1 for _, _, _, t in windows if t > 0)
    return {
        "symbol": symbol,
        "files": n_files,
        "rows": n_rows,
        "bars_evaluated": len(net),
        "net_total": float((1 + net).prod() - 1),
        "bh_total": float((1 + bh).prod() - 1),
        "net_sharpe": sharpe(net),
        "bh_sharpe": sharpe(bh),
        "windows": windows,
        "positive_windows": positives,
        "pass_windows": positives >= 4,
    }


def main():
    n_checked, bad = verify_checksums()
    if bad:
        raise SystemExit(f"Checksum mismatch, aborting: {bad}")
    results = [evaluate(s) for s in ("BTCUSDT", "ETHUSDT")]
    passes = all(r["pass_windows"] and r["net_sharpe"] > 0 for r in results)

    lines = ["# prereg-v2 results", "",
             f"Checksums verified: {n_checked} files, 0 mismatches.",
             f"Lookback: {RUN_LOOKBACK} bars. Cost per side: {COST_PER_SIDE:.4%}. Walk-forward windows: {N_WINDOWS}.", ""]
    for r in results:
        lines += [f"## {r['symbol']}", "",
                  f"- Files: {r['files']}, rows: {r['rows']}, bars evaluated: {r['bars_evaluated']}",
                  f"- Net total return: {r['net_total']:.2%}  (buy-and-hold: {r['bh_total']:.2%})",
                  f"- Net Sharpe: {r['net_sharpe']:.3f}  (buy-and-hold: {r['bh_sharpe']:.3f})",
                  f"- Positive windows: {r['positive_windows']} of {N_WINDOWS}  (criterion: at least 4)", "",
                  "| window | start | end | net return |", "|---|---|---|---|"]
        for k, s, e, t in r["windows"]:
            lines.append(f"| {k} | {s} | {e} | {t:.2%} |")
        lines.append("")
    lines += [f"**Verdict under prereg-v2: {'ACCEPTED' if passes else 'REJECTED'}**", ""]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()




