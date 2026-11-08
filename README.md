# Crypto Quant Research

A validation-first study of systematic crypto trading signals. The objective is to determine whether evidence is strong enough to trust, not to optimize a backtest into looking profitable.

## Current status (2026-11-08)

- **prereg-v1: REJECTED.** The 6-bar lookback failed the pre-registered net-return and Sharpe criteria.
- **prereg-v2: REJECTED.** The 42-bar lookback also failed the net criteria on the same 2022-01 to 2026-10 historical sample. This was not an independent out-of-sample test.
- **prereg-v3-diagnostic: GROSS-EDGE DIAGNOSTIC ONLY.** Returns before costs were positive under the diagnostic rule, but the same historical data had already been used in v1 and v2. This is not evidence of a tradable strategy after costs.
- **prereg-v4-forward: SUPERSEDED.** Preserved as research history; no result was produced.
- **prereg-v5-forward: FROZEN, NOT YET EVALUATED.** The registered period is 2026-11-01 through 2027-01-31. Evaluate only after January 2027 data is published and checksummed, no earlier than early February 2027. Do not alter the frozen rule or criteria after observing forward data.
- **Parameter sensitivity diagnostic:** scripts/stability_v3.py was run on the reused 2022-2026 data for lookbacks 21, 42, 63, and 84. This is exploratory only and does not modify v5. See results/diagnostics/stability_v3_parameter_sensitivity.csv.
- **Prior evidence relevant to v5:** at lookback 42, the exploratory common-range diagnostic reported net Sharpe of -0.0468 for BTC and -0.0097 for ETH. On the reused 2022-2026 sample, this is evidence that no positive net-Sharpe edge was observed at the frozen lookback after the registered cost model; it is not a forecast or an independent prior-data test.
- **v5 criteria:** the frozen prereg-v5-forward tag requires at least 4 of 6 positive net-return windows for each asset and full-period net Sharpe above zero for both assets. It does not require 5/6 windows, outperformance versus buy-and-hold, or a -15% drawdown cap. The benchmark is reported for context only; it is not an acceptance criterion in the frozen file.

## Research protocol

1. **Pre-registration:** write the hypothesis, signal rule, evaluation period, costs, and success/failure criteria before running the test.
2. **Immutable experiment history:** retain tagged preregistrations and results; do not rewrite a frozen specification to fit observed outcomes.
3. **Data integrity:** verify monthly raw files against SHA-256 hashes recorded in data/CHECKSUMS.txt.
4. **Data quality:** inspect gaps, duplicate candles, invalid timestamps, and impossible prices.
5. **Timestamp normalization:** Binance files in this dataset use milliseconds through 2024-12 and microseconds from 2025-01 onward. The v5 evaluator normalizes both formats to UTC before ordering and checking the forward period.
6. **Leakage checks:** features must use only information available at decision time. Automated checks and mutation checks are documented separately.
7. **Costs:** include the registered fee/slippage convention in confirmatory backtests. Gross-return runs are explicitly diagnostic only.
8. **Walk-forward reporting:** report each window and the full-period metrics, including negative results.
9. **Forward evaluation:** run the frozen v5 specification without changing code or criteria after forward data becomes available.

Any new hypothesis or parameter choice requires a separately documented experiment. Historical sensitivity analysis on a reused sample is not a license to tune the frozen forward test.

## Reproduction

From the repository root, with dependencies in requirements.txt installed:

    python -m pytest -q
    python scripts/run_prereg_v1.py
    python scripts/run_prereg_v2.py
    python scripts/run_prereg_v3_diagnostic.py
    python scripts/stability_v3.py

The v1-v3 scripts reproduce historical experiments; they do not constitute independent evidence. Do **not** run them expecting a v5 forward result.

After the 2026-11, 2026-12, and 2027-01 monthly files for both assets are published, place them in data/raw/, append their SHA-256 entries to data/CHECKSUMS.txt, and verify all listed files. Then run:

    python scripts/evaluate_prereg_v5.py

The evaluator aborts if required forward files are absent from the checksum manifest, any checksum fails, timestamps are duplicated after normalization, forward 4-hour bars are missing, or there is insufficient warm-up history. Its synthetic-data behavior and registered decision logic are covered by tests. The evaluator does not tune parameters or thresholds.

Raw monthly data is not committed to this repository. See data/README.md for the expected local layout and data/CHECKSUMS.txt for the recorded hashes.

## Known limitations / follow-up

- The historical dataset was reused in v1, v2, v3, and the parameter sensitivity diagnostic.
- The transaction-cost model is fixed and simplified; it does not model market impact or execution latency.
- Historical result tables now show UTC ISO-8601 window start/end timestamps instead of row indices. This was a reporting-only correction; reported metrics and verdicts were not recalculated.
- The v5 test covers three months and has limited statistical power; a pass would still require independent confirmation.
- CI has not yet been configured for this repository.
- The frozen PRE_REGISTRATION_v5_forward.md status line still says it is to be frozen, although the existing prereg-v5-forward tag confirms the freeze. The frozen file is intentionally unchanged to preserve tagged contents; this metadata inconsistency is recorded for transparency.


## Pre-committed interpretation and data-gap policy (2026-11-08)

- The window-count component alone (at least 4 positive windows out of 6) has probability 22/64 = 34.375% under an idealized null where each window is independent and equally likely to be positive or negative. This is **not** the probability that the full v5 test passes: the registered full-test rule also requires net Sharpe > 0 for both assets, and window outcomes/Sharpe are not independent. Report 34.4% only as a simple reference for the window-count component, not as a calibrated false-positive rate.
- Given the prior reused-sample lookback-42 net Sharpes near zero (BTC -0.0468; ETH -0.0097), a v5 **PASS** will be described as “meets the pre-registered threshold in this single three-month forward test; weak, preliminary evidence, not confirmation of a robust edge.” It will not be called proof or validation. A **REJECTED** result means the frozen success criteria were not met in this forward test; it is a decisive protocol outcome for this specification/period, but not proof that no strategy edge can ever exist. Any further hypothesis requires a separately preregistered test.
- **Strict missing-data policy:** the evaluator requires every expected 4-hour UTC timestamp in the full forward period for each asset. If even one expected bar is missing, or an unexpected timestamp appears in the period, evaluation aborts with an error before producing a verdict. It does not interpolate, silently drop bars, score only available windows, or declare a window invalid and continue. First verify the source publication/download and checksums; if a complete, verifiable series cannot be obtained, record “not evaluable due to data integrity/completeness” and do not issue PASS/REJECTED. This policy is intentionally strict and is covered by a synthetic missing-bar test.
