import pandas as pd

from research.phase12_zenodo_pilot import (
    RISK_PROFILES,
    variant_grid,
    data_gate,
    _last_thursday,
    _utc_naive,
)


def test_variant_count_is_preregistered():
    assert len(variant_grid()) == 144


def test_last_thursday():
    assert _last_thursday(2020, 1) == pd.Timestamp("2020-01-30")
    assert _last_thursday(2020, 4) == pd.Timestamp("2020-04-30")


def test_utc_normalization_from_nse_local_time():
    x = pd.Series(pd.to_datetime(["2020-01-02 09:15:00", "2020-01-02 09:16:00"]))
    y = _utc_naive(x)
    assert str(y.iloc[0]) == "2020-01-02 03:45:00"


def test_data_gate_passes_reasonable_overlap():
    dt = pd.date_range("2019-01-01", periods=400, freq="D")
    f = pd.DataFrame({"datetime": dt, "futures_close": 100.0})
    s = pd.DataFrame({"datetime": dt, "spot_close": 100.0})
    g = data_gate(f, s)
    assert g["gate"] == "PASS"


def test_risk_profiles_fixed():
    assert RISK_PROFILES == (
        {"stop_pct": 0.30, "target_pct": 0.60},
        {"stop_pct": 0.50, "target_pct": 1.00},
    )
