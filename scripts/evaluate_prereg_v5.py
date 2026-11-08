"""Evaluate the frozen prereg-v5 forward test; no parameter tuning or result-dependent edits.

Run only after all six forward monthly files are published and checksummed.
Expected filenames: SYMBOL-4h-YYYY-MM.csv in data/raw/.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CHECKSUMS = ROOT / "data" / "CHECKSUMS.txt"
OUT = ROOT / "results" / "prereg-v5-forward.md"
START = pd.Timestamp("2026-11-01T00:00:00Z")
END = pd.Timestamp("2027-02-01T00:00:00Z")
LOOKBACK = 42
COST_PER_SIDE = 0.0015
BARS_PER_YEAR = 2190
N_WINDOWS = 6
FORWARD_MONTHS = ("2026-11", "2026-12", "2027-01")
ASSETS = ("BTCUSDT", "ETHUSDT")


def normalize_open_time(values: pd.Series) -> pd.Series:
    """Normalize Binance millisecond or microsecond epoch timestamps to UTC."""
    numeric = pd.to_numeric(values, errors="raise").astype("int64")
    is_microseconds = numeric >= 10**14
    milliseconds = numeric.where(~is_microseconds, numeric // 1000)
    return pd.to_datetime(milliseconds, unit="ms", utc=True)


def verify_checksums() -> int:
    expected = {}
    with CHECKSUMS.open(encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            digest, relative = line.split("  ", 1)
            expected[Path(relative).name] = digest.lower()

    required = {
        f"{asset}-4h-{month}.csv"
        for asset in ASSETS
        for month in FORWARD_MONTHS
    }
    missing_entries = sorted(required - expected.keys())
    if missing_entries:
        raise RuntimeError(f"Forward files are not yet checksummed: {missing_entries}")

    missing_files, mismatches = [], []
    for name, digest in expected.items():
        path = RAW / name
        if not path.is_file():
            missing_files.append(name)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            mismatches.append(name)
    if missing_files or mismatches:
        raise RuntimeError(
            f"Checksum verification failed; missing={missing_files}; mismatched={mismatches}"
        )
    return len(expected)


def load_close(asset: str) -> pd.Series:
    paths = sorted(RAW.glob(f"{asset}-4h-*.csv"))
    if not paths:
        raise FileNotFoundError(f"No raw monthly files found for {asset}")

    frames = []
    for path in paths:
        frame = pd.read_csv(path, header=None, usecols=[0, 4])
        frame.columns = ["open_time", "close"]
        frame["open_time"] = normalize_open_time(frame["open_time"])
        frame["close"] = pd.to_numeric(frame["close"], errors="raise").astype(float)
        frames.append(frame)

    data = pd.concat(frames, ignore_index=True).sort_values("open_time")
    if data["open_time"].duplicated().any():
        duplicates = data.loc[data["open_time"].duplicated(), "open_time"].astype(str).tolist()[:5]
        raise ValueError(f"Duplicate normalized timestamps for {asset}: {duplicates}")
    if not np.isfinite(data["close"]).all() or (data["close"] <= 0).any():
        raise ValueError(f"Invalid close prices found for {asset}")

    close = data.set_index("open_time")["close"]
    if close.index.tz is None or not close.index.is_monotonic_increasing:
        raise ValueError(f"Timestamp index is not sorted UTC for {asset}")
    return close


def sharpe(returns: pd.Series) -> float:
    r = returns.dropna()
    sd = r.std(ddof=1)
    if len(r) < 2 or not np.isfinite(sd) or sd <= 0:
        return float("nan")
    return float(r.mean() / sd * np.sqrt(BARS_PER_YEAR))


def compute_forward_metrics(close: pd.Series) -> dict:
    """Compute registered v5 metrics from historical warm-up plus forward closes."""
    close = close.sort_index()
    if close.index.has_duplicates:
        raise ValueError("Close series has duplicate timestamps")
    if close.index.tz is None:
        raise ValueError("Close index must be timezone-aware UTC")

    expected_forward = pd.date_range(START, END, freq="4h", inclusive="left")
    observed_forward = close.index[(close.index >= START) & (close.index < END)]
    if not observed_forward.equals(expected_forward):
        missing = expected_forward.difference(observed_forward)
        extra = observed_forward.difference(expected_forward)
        raise ValueError(
            f"Forward timestamps must be complete 4h bars; missing={list(missing[:5])}, "
            f"extra={list(extra[:5])}, observed={len(observed_forward)}, "
            f"expected={len(expected_forward)}"
        )
    prior = close.loc[close.index < START]
    if len(prior) < LOOKBACK + 1:
        raise ValueError("Insufficient pre-period history for 42-bar lookback and lag")

    signal = (close / close.shift(LOOKBACK) - 1.0 > 0).astype(float)
    signal = signal.where(close.shift(LOOKBACK).notna())
    position = signal.shift(1)
    bar_returns = close.pct_change()
    gross = position * bar_returns
    turnover = position.diff().abs()
    turnover.iloc[0] = abs(position.iloc[0]) if pd.notna(position.iloc[0]) else 0.0
    net = gross - COST_PER_SIDE * turnover.fillna(0.0)

    forward_net = net.loc[(net.index >= START) & (net.index < END)]
    forward_gross = gross.loc[(gross.index >= START) & (gross.index < END)]
    if forward_net.isna().any() or len(forward_net) != len(expected_forward):
        raise ValueError("Net forward return series contains missing values or wrong length")

    windows = []
    for i, idx in enumerate(np.array_split(np.arange(len(forward_net)), N_WINDOWS), start=1):
        segment = forward_net.iloc[idx]
        windows.append({
            "window": i,
            "start_utc": segment.index[0].isoformat(),
            "end_utc": segment.index[-1].isoformat(),
            "net_return_pct": float(((1.0 + segment).prod() - 1.0) * 100.0),
        })

    # Benchmark includes the return into the first forward close and one entry/exit cost.
    benchmark = bar_returns.loc[(bar_returns.index >= START) & (bar_returns.index < END)].copy()
    benchmark.iloc[0] -= COST_PER_SIDE
    benchmark.iloc[-1] -= COST_PER_SIDE

    return {
        "bars": len(forward_net),
        "net_total_return_pct": float(((1.0 + forward_net).prod() - 1.0) * 100.0),
        "net_sharpe": sharpe(forward_net),
        "gross_total_return_pct": float(((1.0 + forward_gross).prod() - 1.0) * 100.0),
        "benchmark_return_pct": float(((1.0 + benchmark).prod() - 1.0) * 100.0),
        "benchmark_sharpe": sharpe(benchmark),
        "positive_windows": sum(w["net_return_pct"] > 0 for w in windows),
        "windows": windows,
    }


def evaluate_result_set(close_by_asset: dict[str, pd.Series]) -> dict:
    results = {asset: compute_forward_metrics(close_by_asset[asset]) for asset in ASSETS}
    passed = all(
        results[asset]["positive_windows"] >= 4 and results[asset]["net_sharpe"] > 0
        for asset in ASSETS
    )
    return {"assets": results, "verdict": "PASS" if passed else "REJECTED"}


def render_report(result: dict, checksums_verified: int) -> str:
    lines = [
        "# prereg-v5-forward results",
        "",
        "Evaluation of the frozen prereg-v5-forward specification. No thresholds or parameters were changed.",
        "",
        f"Checksums verified: {checksums_verified} files, 0 mismatches.",
        f"Forward period: {START.isoformat()} through {(END - pd.Timedelta(hours=4)).isoformat()} (UTC).",
        f"Bars per asset: {next(iter(result['assets'].values()))['bars']}.",
        "",
        "## Registered success criteria",
        "",
        "- BTCUSDT: net return positive in at least 4 of 6 windows.",
        "- ETHUSDT: net return positive in at least 4 of 6 windows.",
        "- Full-period annualized net Sharpe above 0 for both assets.",
        "",
    ]
    for asset, metrics in result["assets"].items():
        lines.extend([
            f"## {asset}",
            "",
            f"- Net total return: {metrics['net_total_return_pct']:.4f}%",
            f"- Net Sharpe: {metrics['net_sharpe']:.6f}",
            f"- Gross total return (diagnostic): {metrics['gross_total_return_pct']:.4f}%",
            f"- Buy-and-hold return after entry/exit costs: {metrics['benchmark_return_pct']:.4f}%",
            f"- Buy-and-hold Sharpe: {metrics['benchmark_sharpe']:.6f}",
            f"- Positive net windows: {metrics['positive_windows']} of {N_WINDOWS}",
            "",
            "| Window | Start UTC | End UTC | Net return |",
            "|---:|---|---|---:|",
        ])
        for w in metrics["windows"]:
            lines.append(
                f"| {w['window']} | {w['start_utc']} | {w['end_utc']} | "
                f"{w['net_return_pct']:.4f}% |"
            )
        lines.append("")
    lines.extend([
        f"**Verdict under prereg-v5-forward: {result['verdict']}**",
        "",
        "This is a single three-month forward evaluation and does not establish general robustness. "
        "Results are reported as computed, including negative outcomes.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    checksums_verified = verify_checksums()
    close_by_asset = {asset: load_close(asset) for asset in ASSETS}
    result = evaluate_result_set(close_by_asset)
    report = render_report(result, checksums_verified)
    OUT.write_text(report, encoding="utf-8", newline="\n")
    print(report)
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
