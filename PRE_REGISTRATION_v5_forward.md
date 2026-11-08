# Pre-registration v5 (forward test, shortened): BTC/ETH momentum, lookback 42, with costs

Version: prereg-v5-forward
Status: to be FROZEN at git tag `prereg-v5-forward` before any forward data exists.
Supersedes: prereg-v4-forward (six months). v4 is kept in the repository as history. No result was produced from it.

## 1. Why a forward test

The 2022-2026 data has been used in three experiments. This test uses only data after the freeze date.

## 2. Data

- Assets: BTCUSDT and ETHUSDT, Binance spot, 4h candles (UTC).
- Forward period: 2026-11-01 00:00 UTC to 2027-01-31 23:59 UTC (three calendar months, about 540 bars per asset).
- Source: Binance Public Data monthly files for 2026-11, 2026-12, and 2027-01. Each file is hashed with SHA-256 when downloaded, and the hashes are committed before the evaluation is run.
- Warm-up: the rule needs 42 prior closes, taken from the frozen 2022-2026 files (`data/CHECKSUMS.txt`, commit `8a93c25`). Returns are evaluated only from 2026-11-01 onward.

## 3. Rule (unchanged from prereg-v2 and v4)

- Lookback: 42 bars (one week). Long-only.
- Signal at close of bar t: 1 if close_t / close_(t-42) - 1 > 0, else 0.
- Position over bar t: signal at close of bar t-1.
- Net return per bar: position_t * bar_return_t - 0.0015 * |position_t - position_(t-1)|.
- Costs: 0.10% fee + 0.05% slippage per side.

## 4. Benchmark

Buy-and-hold over the same forward period, with one entry and one exit cost.

## 5. Evaluation

- Six equal, consecutive windows of about 90 bars each (about 15 days). Windows are defined by bar count, so each asset has the same window boundaries.
- For each window: compounded net return.
- Full forward period: annualized net Sharpe, 2,190 bars per year, risk-free rate 0.

## 6. Success criteria (all must hold)

1. BTC: net return positive in at least 4 of the 6 windows.
2. ETH: net return positive in at least 4 of the 6 windows.
3. Full-period net Sharpe above 0 for both assets.

## 7. Limitations stated before the run

- A three-month test has less statistical power than a six-month test. A pass or a failure is weaker evidence than in v4. The shorter length was chosen to get a result sooner.
- Each window is about 15 days, so single windows are noisy.
- A pass would still need independent confirmation.

## 8. Failure policy

If any criterion fails, the strategy is rejected on forward data. No change to lookback, costs, windows, or thresholds is allowed.

## 9. Timeline

- Freeze: 2026-11-08 (this document).
- Runner code is committed before 2027-02-01 with no change to the rule and no results.
- Evaluation: no earlier than the day after the 2027-01 monthly files are published (early February 2027).

## 10. Reporting

Per asset, per window, full-period figures, and the benchmark. Results are reported as written, including negative results.
