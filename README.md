# Crypto Quant Research

A validation-first study of systematic crypto trading signals. The goal is to decide whether the evidence for a signal is strong enough to trust, not to find a strategy that backtests well.

## Method

Every hypothesis follows the same protocol:

1. **Pre-registration:** hypothesis, signal rule, success criteria, and data period are written down before results are seen (see `PRE_REGISTRATION.md`).
2. **Data freeze:** the raw data file is hashed with SHA-256 and the hash is recorded.
3. **Data quality checks:** gaps, duplicate candles, impossible prices. Each decision is logged.
4. **Leakage checks:** every feature uses only information available at decision time. These checks are automated tests.
5. **Backtest with costs:** commissions and slippage are included explicitly.
6. **Walk-forward evaluation:** several consecutive out-of-sample windows, not a single split.
7. **Report:** the result is reported as written, including negative results.

No specification changes after seeing results. Any change requires a new pre-registered experiment.

## Status

- [ ] Pre-registration (draft in `PRE_REGISTRATION.md`, not yet frozen)
- [ ] Data download and freeze
- [ ] Data quality report
- [ ] Leakage tests
- [ ] Baseline backtest
- [ ] Walk-forward evaluation
- [ ] Final report

## Data

Raw data is **not** committed to this repository. See `data/README.md` for the download source and the expected file layout.
