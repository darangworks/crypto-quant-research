import numpy as np
import pandas as pd
import pytest

from src.momentum import positions
from scripts import stability_v3


def assert_causal(position_fn, close, lookback, t):
    baseline = position_fn(close, lookback)
    changed = close.copy()
    changed.iloc[t + 1:] = changed.iloc[t + 1:] * 1.5
    perturbed = position_fn(changed, lookback)
    pd.testing.assert_series_equal(baseline.iloc[:t + 1], perturbed.iloc[:t + 1])


def test_stability_evaluate_produces_expected_metrics_on_synthetic_series():
    rng = np.random.default_rng(17)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, 1500))))
    result = stability_v3.evaluate(close, lookback=42, common_start=close.index[85])
    assert result["lookback"] == 42
    assert result["bars_evaluated_common_range"] > 1000
    assert np.isfinite(result["gross_sharpe"])
    assert np.isfinite(result["net_sharpe"])
    assert len(result["gross_window_returns_pct"].split(";")) == 6
    assert len(result["net_window_returns_pct"].split(";")) == 6


def test_stability_position_pipeline_is_causal():
    rng = np.random.default_rng(8)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 500))))
    assert_causal(positions, close, lookback=42, t=250)


def test_mutation_with_future_leak_is_detected():
    close = pd.Series(np.full(300, 100.0))

    def deliberately_leaky_positions(prices, lookback):
        # Intentional mutation for the test only: reads the next bar's close.
        return prices.shift(-1).gt(prices).astype(float)

    with pytest.raises(AssertionError):
        assert_causal(deliberately_leaky_positions, close, lookback=42, t=150)


def test_future_leak_mutation_changes_diagnostic_sharpe(monkeypatch):
    rng = np.random.default_rng(31)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0001, 0.01, 1500))))
    common_start = close.index[85]
    causal = stability_v3.evaluate(close, lookback=42, common_start=common_start)

    def deliberately_leaky_positions(prices, lookback):
        return prices.shift(-1).gt(prices).astype(float)

    monkeypatch.setattr(stability_v3, "positions", deliberately_leaky_positions)
    mutated = stability_v3.evaluate(close, lookback=42, common_start=common_start)
    assert not np.isclose(causal["gross_sharpe"], mutated["gross_sharpe"])
