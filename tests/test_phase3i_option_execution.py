import pandas as pd

from research.phase3i_option_execution import (
    HOLDS,
    EXPIRIES,
    WIDTH_STEPS,
    SIGNAL_SPECS,
    build_signal_events,
    signal_variant_key,
)


def test_option_grid_is_24_variants():
    assert len(SIGNAL_SPECS) == 2
    assert EXPIRIES == ("WEEK", "MONTH")
    assert WIDTH_STEPS == (1, 2)
    assert HOLDS == (5, 10, 15)
    assert len(SIGNAL_SPECS) * len(EXPIRIES) * len(WIDTH_STEPS) * len(HOLDS) == 24


def test_signal_variant_keys_are_stable():
    assert signal_variant_key(SIGNAL_SPECS[0]) == (
        '{"feature": "lead_gap", "lookback": 3, "mode": "continuation", "threshold_bps": 10.0}'
    )


def test_signal_builder_uses_first_event_per_day():
    idx = pd.date_range("2019-01-02 09:30", periods=4, freq="min")
    spot = pd.DataFrame({
        "datetime": idx,
        "trade_date": idx.date,
        "close": [100, 100.1, 100.2, 100.3],
    })
    fut = spot.copy()
    fut["close"] = [100, 100.2, 100.4, 100.6]
    out = build_signal_events(spot, fut)
    assert out["trade_date"].nunique() <= 1
