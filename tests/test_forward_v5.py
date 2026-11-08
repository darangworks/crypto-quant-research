import numpy as np
import pandas as pd
import pytest

from scripts import evaluate_prereg_v5 as v5


def synthetic_close(seed=23):
    rng = np.random.default_rng(seed)
    history_start = v5.START - pd.Timedelta(hours=4 * 100)
    index = pd.date_range(history_start, v5.END - pd.Timedelta(hours=4), freq="4h")
    returns = rng.normal(0.00015, 0.006, len(index))
    close = 100.0 * np.exp(np.cumsum(returns))
    return pd.Series(close, index=index, name="close")


def test_mixed_binance_timestamp_units_normalize_to_same_utc_time():
    milliseconds = pd.Series([1735689600000], dtype="int64")
    microseconds = pd.Series([1735689600000000], dtype="int64")
    assert v5.normalize_open_time(milliseconds).equals(v5.normalize_open_time(microseconds))


def test_forward_evaluator_returns_six_equal_windows_and_full_period():
    metrics = v5.compute_forward_metrics(synthetic_close())
    assert metrics["bars"] == 552
    assert len(metrics["windows"]) == 6
    assert [w["window"] for w in metrics["windows"]] == [1, 2, 3, 4, 5, 6]
    assert all(w["start_utc"].endswith("+00:00") for w in metrics["windows"])
    assert all(np.isfinite(w["net_return_pct"]) for w in metrics["windows"])
    assert np.isfinite(metrics["net_sharpe"])


def test_forward_evaluator_rejects_a_missing_bar():
    close = synthetic_close()
    missing = v5.START + pd.Timedelta(hours=4 * 20)
    close = close.drop(missing)
    with pytest.raises(ValueError, match="complete 4h bars"):
        v5.compute_forward_metrics(close)


def test_forward_evaluator_requires_timezone_aware_index():
    close = synthetic_close()
    close.index = close.index.tz_localize(None)
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        v5.compute_forward_metrics(close)


def test_prereg_verdict_requires_both_assets_to_meet_both_criteria(monkeypatch):
    good = {
        "bars": 552,
        "net_total_return_pct": 1.0,
        "net_sharpe": 0.1,
        "gross_total_return_pct": 2.0,
        "benchmark_return_pct": 0.5,
        "benchmark_sharpe": 0.05,
        "positive_windows": 4,
        "windows": [],
    }
    monkeypatch.setattr(v5, "compute_forward_metrics", lambda close: dict(good))
    result = v5.evaluate_result_set({"BTCUSDT": pd.Series(dtype=float), "ETHUSDT": pd.Series(dtype=float)})
    assert result["verdict"] == "PASS"

    bad_eth = dict(good, positive_windows=3)
    monkeypatch.setattr(
        v5, "compute_forward_metrics",
        lambda close: dict(good if close.name == "BTCUSDT" else bad_eth),
    )
    result = v5.evaluate_result_set({
        "BTCUSDT": pd.Series(dtype=float, name="BTCUSDT"),
        "ETHUSDT": pd.Series(dtype=float, name="ETHUSDT"),
    })
    assert result["verdict"] == "REJECTED"
