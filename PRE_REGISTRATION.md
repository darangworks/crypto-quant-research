# Pre-registration (DRAFT, not frozen)

Status: draft. This document must be frozen (committed with a tag) before any backtest result is viewed.

## Scope
- Assets: BTC/USDT, ETH/USDT (Binance spot)
- Timeframe: 4-hour candles
- Data period: 2022-01-01 to the freeze date (to be set)
- Data source: Binance Public Data, downloaded once and hashed (SHA-256 recorded at freeze)

## Hypothesis (to be finalized)
Placeholder: a simple momentum signal on 4h returns predicts the next 4h return. This is a placeholder, not a commitment; the final hypothesis and rule must be written here before freezing.

## Decision rules (to be finalized)
- Signal computed from data up to the close of candle t only.
- Position taken at the open of candle t+1.
- Costs: commission and slippage values to be stated explicitly before freezing.

## Success criteria (to be finalized)
- Out-of-sample performance must be positive in a stated fraction of walk-forward windows.
- Result must hold on both assets separately.
- Thresholds are stated numerically here before freezing.

## Failure policy
If the criteria are not met, the hypothesis is rejected and reported. No parameter tuning to rescue it; any new idea needs a new pre-registration.
