import numpy as np
import pandas as pd

from src.momentum import positions, signal, net_returns


def synthetic_close(n=500, seed=0):
    rng = np.random.default_rng(seed)
    steps = rng.normal(0, 0.01, n)
    return pd.Series(100 * np.exp(np.cumsum(steps)))


def test_position_does_not_depend_on_future_closes():
    close = synthetic_close()
    base = positions(close)
    t = 200
    perturbed = close.copy()
    perturbed.iloc[t + 1:] = perturbed.iloc[t + 1:] * 1.5
    changed = positions(perturbed)
    pd.testing.assert_series_equal(base.iloc[: t + 1], changed.iloc[: t + 1])


def test_signal_uses_only_past_and_current_closes():
    close = synthetic_close()
    base = signal(close)
    # For every bar t, replacing ALL future closes must not change signal_t.
    for t in range(10, len(close) - 2):
        perturbed = close.copy()
        perturbed.iloc[t + 1 :] = 1e9
        assert signal(perturbed).iloc[t] == base.iloc[t], f"leak at bar {t}"


def test_position_is_one_bar_lagged_signal():
    close = synthetic_close()
    pd.testing.assert_series_equal(positions(close), signal(close).shift(1))


def test_net_return_position_unaffected_by_own_bar_shock():
    close = synthetic_close()
    t = 150
    pos_before = positions(close).iloc[t]
    perturbed = close.copy()
    perturbed.iloc[t] = perturbed.iloc[t] * 0.5
    pos_after = positions(perturbed).iloc[t]
    assert pos_before == pos_after


def test_costs_charged_on_position_change_only():
    close = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109.0])
    net = net_returns(close)
    pos = positions(close)
    flips = pos.diff().abs().fillna(pos.abs())
    gross = pos * close.pct_change()
    expected = gross - 0.0015 * flips
    pd.testing.assert_series_equal(net, expected)
