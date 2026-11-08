# Pre-registration v3 (diagnostic): BTC/ETH momentum, lookback 42, zero costs

Version: prereg-v3-diagnostic
Status: to be FROZEN at git tag `prereg-v3-diagnostic` before the run.
Type: DIAGNOSTIC. This experiment does not accept or reject the strategy. It only decides whether a gross edge exists before costs.

## 1. Question

prereg-v2 (lookback 42, with costs) was rejected. Does the signal have any positive return before costs? This separates two explanations:
- costs are the main reason for the loss (signal has gross edge), or
- the signal has no edge even before costs (costs are not the explanation).

## 2. Data and rule (unchanged from prereg-v2)

- Assets: BTCUSDT and ETHUSDT, 4h, 2022-01-01 to 2026-10-31, the frozen files in `data/CHECKSUMS.txt`.
- Lookback: 42 bars. Long-only. Position over bar t is the signal at close of bar t-1.
- Gross return per bar: position_t * bar_return_t.
- Costs: zero. This is the only change from v2.
- Walk-forward: the same 6 equal consecutive windows as v2.

## 3. Also reported (descriptive)

- Number of position changes (turnover) for each asset.
- Average cost per bar that v2 paid, computed as the difference between v2 net and this gross result.

## 4. Pre-registered interpretation rule (not an acceptance rule)

Let G be the number of windows with positive gross return, for each asset separately, and S the full-period gross Sharpe.

- If G is at least 4 for both assets and S is above 0 for both: the signal has a gross edge. Costs are the binding constraint, and a future experiment should test lower-turnover designs under the same cost assumptions.
- Otherwise: the signal has no gross edge at this lookback. Costs cannot explain the rejection, and reducing turnover alone will not make the strategy pass.

This rule is written before the run. It does not change the v2 verdict, which remains REJECTED.

## 5. Reporting

Gross results per asset and per window, turnover, the average cost per bar, and the interpretation above. The output is labeled as diagnostic.
