# Pre-registration: P005 — Crypto Time-Series Momentum (BTC/ETH, 4h)

Version: prereg-v1
Status: FROZEN at the git tag `prereg-v1`. Any change after freezing requires a new pre-registration (prereg-v2) and a new experiment.

## 1. Data

- Assets: BTCUSDT and ETHUSDT, Binance spot.
- Timeframe: 4-hour candles (UTC).
- Period: 2022-01-01 00:00 UTC to 2026-10-31 23:59 UTC.
- Files: the 116 monthly CSVs listed in `data/CHECKSUMS.txt`. Raw files are not committed. Any file whose SHA-256 does not match is excluded and the exclusion is reported.
- Columns used: `close`, `open_time`. Nothing else.

## 2. Hypothesis

Time-series momentum: if the price rose over the past 6 bars (24 hours), the next bar's return is more likely positive than negative, and a long-only position taken on that signal earns a positive net return after costs.

The lookback of 6 bars is fixed here and is not tuned.

## 3. Signal and position (no look-ahead)

For each bar t:

- `past_return_t = close_t / close_(t-6) - 1`
- `signal_t = 1` if `past_return_t > 0`, else `0` (long or flat; no shorting)
- Position held during bar t+1: `position_(t+1) = signal_t`

The position for bar t+1 is decided using only data up to the close of bar t. The position is applied to the return from close_t to close_(t+1).

## 4. Returns and costs

- `bar_return_t = close_t / close_(t-1) - 1`
- `gross_t = position_t * bar_return_t`
- Cost per side: 0.10% fee + 0.05% slippage = 0.15%.
- `cost_t = 0.0015 * |position_t - position_(t-1)|`
- `net_t = gross_t - cost_t`

Entry into the first position is charged at the same rate.

## 5. Benchmark

Buy-and-hold of the same asset over the same period, with one entry cost and one exit cost.

## 6. Evaluation

- Full period: annualized Sharpe ratio of net returns, using 2,190 bars per year (6 per day × 365), with the risk-free rate set to 0.
- Walk-forward: the period is split into 6 equal, consecutive, non-overlapping windows of about 9.7 months each. No parameters are fitted in any window, so the windows measure stability over time, not parameter selection.

## 7. Success criteria (all must hold)

1. For BTC separately: net return is positive in at least 4 of the 6 windows.
2. For ETH separately: net return is positive in at least 4 of the 6 windows.
3. Full-period net Sharpe ratio is greater than 0 for both assets.
4. Leakage tests (section 8) pass before any backtest result is viewed.

## 8. Leakage tests (required before the backtest)

- The position for bar t depends only on closes up to bar t-1.
- Changing any close after bar t must not change the position at bar t. This is tested by perturbing future prices and checking that earlier positions do not change.
- The signal uses no future column (no `close_(t+1)` or later).

## 9. Failure policy

If any criterion fails, the hypothesis is rejected and reported as rejected. No change to lookback, costs, windows, or thresholds is allowed to rescue it. A different lookback or rule is a new experiment with its own pre-registration.

## 10. Reporting

The result is reported as written, including negative results. Per-window and per-asset results are shown, not only the full-period figure.
