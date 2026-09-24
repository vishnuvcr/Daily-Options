import pandas as pd

from research.phase13_late_day_volatility_acceleration import (
    variant_grid, _feature_table, _signal_rows
)


def test_variant_count():
    assert len(variant_grid()) == 192


def test_feature_barrier_uses_ist():
    spot = pd.DataFrame({
        "datetime": pd.to_datetime(["2019-01-02 03:44:00", "2019-01-02 03:45:00"]),
        "spot_close": [100.0, 101.0],
    })
    x = _feature_table(spot)
    assert x.iloc[-1]["trade_time_ist"] == "09:15:00"


def test_signal_requires_late_day_time():
    row = pd.DataFrame({
        "datetime": pd.to_datetime(["2019-01-02 09:45:00"]),
        "spot_close": [101.0],
        "trade_date": [pd.Timestamp("2019-01-02").date()],
        "trade_time_ist": ["09:45:00"],
        "z10": [2.0],
        "z15": [2.0],
        "rv_percentile": [90.0],
        "prior_30_high": [100.0],
        "prior_30_low": [99.0],
    })
    v = variant_grid()[0]
    assert _signal_rows(row, v).empty
