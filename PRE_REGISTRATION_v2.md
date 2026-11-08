# Pre-registration v2: BTC/ETH 4h time-series momentum, lookback 42

Version: prereg-v2
Status: to be FROZEN at git tag `prereg-v2` before any v2 run.
Relation to v1: prereg-v1 (tag `prereg-v1`) is unchanged and remains the record of the first experiment (REJECTED). This is a new experiment on a new rule.

## 1. Why this experiment

prereg-v1 used a 6-bar lookback. Its trades flipped often, and each flip cost 0.15%. This experiment tests the same signal family with a longer lookback, which should reduce turnover. It is a test of one specific explanation, not a search for the best lookback.

## 2. Important limitation (stated before the run)

The BTC and ETH data (2022-01 to 2026-10) was already used in v1. v2 is therefore a second test on the same data. A pass would be weaker evidence than a pass on fresh data. Results will be reported with this caveat.

To partly address this, the period from 2026-11-01 onward is held out as a forward check. It is reported as information only and is not one of the criteria below.

## 3. Data

- Assets: BTCUSDT and ETHUSDT, Binance spot, 4h candles (UTC).
- Period for the main test: 2022-01-01 to 2026-10-31, the same frozen files as v1 (`data/CHECKSUMS.txt`, commit `8a93c25`).
- Forward holdout (information only): 2026-11-01 onward, not used in any criterion.

## 4. Rule

- Lookback: 42 bars (one week). Fixed here. Not tuned.
- Signal at close of bar t: long (1) if close_t / close_(t-42) - 1 > 0, else 0. Long-only.
- Position over bar t: position_t = signal_(t-1).
- Net return per bar: position_t * bar_return_t - 0.0015 * |position_t - position_(t-1)|.
- Cost: 0.10% fee + 0.05% slippage per side. Same as v1.

## 5. Benchmark

Buy-and-hold of the same asset over the same period, with one entry and one exit cost. Same as v1.

## 6. Evaluation

- Full period: annualized Sharpe of net returns, 2,190 bars per year, risk-free rate 0.
- Walk-forward: 6 equal, consecutive, non-overlapping windows over the main test period. No parameters are fitted in any window.

## 7. Success criteria (all must hold; same bar as v1)

1. BTC: net return positive in at least 4 of 6 windows.
2. ETH: net return positive in at least 4 of 6 windows.
3. Full-period net Sharpe above 0 for both assets.
4. Leakage tests pass (`tests/test_leakage.py`, updated to take the lookback as an argument, with the same checks at 42 bars).

## 8. Failure policy

If any criterion fails, v2 is rejected. No change to the lookback, costs, windows, or thresholds is allowed. Any other lookback is a new pre-registration.

## 9. Reporting

Per asset and per window results, the full-period figures, the buy-and-hold benchmark, and the forward holdout as information only. Negative results are reported as written.
