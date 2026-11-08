import numpy as np
import pandas as pd
import pytest

from src.momentum import positions, signal, net_returns, COST_PER_SIDE


def synthetic_close(n=600, seed=0):
    rng = np.random.default_rng(seed)
    steps = rng.normal(0, 0.01, n)
    return pd.Series(100 * np.exp(np.cumsum(steps)))


@pytest.mark.parametrize("lookback", [6, 42])
def test_position_does_not_depend_on_future_closes(lookback):
    close = synthetic_close()
    base = positions(close, lookback)
    t = 300
    perturbed = close.copy()
    perturbed.iloc[t + 1:] = perturbed.iloc[t + 1:] * 1.5
    changed = positions(perturbed, lookback)
    pd.testing.assert_series_equal(base.iloc[: t + 1], changed.iloc[: t + 1])


@pytest.mark.parametrize("lookback", [6, 42])
def test_signal_uses_only_past_and_current_closes(lookback):
    close = synthetic_close()
    base = signal(close, lookback)
    for t in range(lookback + 2, len(close) - 2):
        perturbed = close.copy()
        perturbed.iloc[t + 1 :] = 1e9
        assert signal(perturbed, lookback).iloc[t] == base.iloc[t], f"leak at bar {t}"


@pytest.mark.parametrize("lookback", [6, 42])
def test_position_is_one_bar_lagged_signal(lookback):
    close = synthetic_close()
    pd.testing.assert_series_equal(positions(close, lookback), signal(close, lookback).shift(1))


@pytest.mark.parametrize("lookback", [6, 42])
def test_position_unaffected_by_own_bar_shock(lookback):
    close = synthetic_close()
    t = 350
    pos_before = positions(close, lookback).iloc[t]
    perturbed = close.copy()
    perturbed.iloc[t] = perturbed.iloc[t] * 0.5
    pos_after = positions(perturbed, lookback).iloc[t]
    assert pos_before == pos_after


def test_costs_charged_on_position_change_only():
    close = pd.Series(np.linspace(100, 130, 60))
    net = net_returns(close, 6)
    pos = positions(close, 6)
    flips = pos.diff().abs().fillna(pos.abs())
    gross = pos * close.pct_change()
    expected = gross - COST_PER_SIDE * flips
    pd.testing.assert_series_equal(net, expected)
