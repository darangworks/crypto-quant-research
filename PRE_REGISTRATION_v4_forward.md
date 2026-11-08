# Pre-registration v4 (forward test): BTC/ETH momentum, lookback 42, with costs

Version: prereg-v4-forward
Status: to be FROZEN at git tag `prereg-v4-forward` before any forward data exists.

## 1. Why a forward test

The 2022-2026 data has now been used in three experiments (v1, v2, and the zero-cost diagnostic). A result on that data cannot be fully trusted. This experiment uses only data from after the freeze date, which no one has seen.

## 2. Data

- Assets: BTCUSDT and ETHUSDT, Binance spot, 4h candles (UTC).
- Forward period: 2026-11-01 00:00 UTC to 2027-04-30 23:59 UTC (six calendar months).
- Source: Binance Public Data monthly files for 2026-11 through 2027-04. Each file is hashed with SHA-256 when downloaded, and the hashes are committed before the evaluation is run.
- Warm-up: the rule needs 42 prior closes. Those come from the frozen 2022-2026 files (`data/CHECKSUMS.txt`, commit `8a93c25`). Returns are evaluated only from 2026-11-01 onward.

## 3. Rule (unchanged from prereg-v2)

- Lookback: 42 bars (one week). Long-only.
- Signal at close of bar t: 1 if close_t / close_(t-42) - 1 > 0, else 0.
- Position over bar t: signal at close of bar t-1.
- Net return per bar: position_t * bar_return_t - 0.0015 * |position_t - position_(t-1)|.
- Costs: 0.10% fee + 0.05% slippage per side.

## 4. Benchmark

Buy-and-hold over the same forward period, with one entry and one exit cost.

## 5. Evaluation

- Six windows, one calendar month each: 2026-11, 2026-12, 2027-01, 2027-02, 2027-03, 2027-04.
- For each window: compounded net return.
- Full forward period: annualized net Sharpe, 2,190 bars per year, risk-free rate 0.

## 6. Success criteria (all must hold)

1. BTC: net return positive in at least 4 of the 6 monthly windows.
2. ETH: net return positive in at least 4 of the 6 monthly windows.
3. Full-period net Sharpe above 0 for both assets.

## 7. Failure policy

If any criterion fails, the strategy is rejected on forward data. No change to lookback, costs, windows, or thresholds is allowed. A pass would still need an independent confirmation, because the rule was chosen after seeing the 2022-2026 data.

## 8. Timeline

- Freeze: 2026-11-08 (this document).
- Runner code is committed before 2027-05-01 with no change to the rule. It contains no results.
- Evaluation: no earlier than the day after the monthly file for 2027-04 is published.

## 9. Reporting

Per asset, per monthly window, full-period figures, and the benchmark. Results are reported as written, including negative results.
