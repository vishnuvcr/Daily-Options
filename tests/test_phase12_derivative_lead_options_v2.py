import pandas as pd

from research.phase12_derivative_lead_options_v2 import build_nearest_contract, data_gate, to_utc_naive


def test_nearest_contract_is_expiry_aware():
    df = pd.DataFrame({
        "datetime": pd.to_datetime(["2025-01-10 09:30:00"] * 2),
        "close": [100.0, 101.0],
        "expiry": pd.to_datetime(["2025-01-30", "2025-02-27"]),
    })
    out = build_nearest_contract(df)
    assert out.iloc[0]["expiry"].isoformat() == "2025-01-30"


def test_data_gate_passes_reasonable_overlap():
    dt = pd.date_range("2025-01-01", periods=400, freq="D")
    f = pd.DataFrame({"datetime": dt, "close": 100.0, "expiry": pd.Timestamp("2026-01-01")})
    s = pd.DataFrame({"datetime": dt, "spot_close": 100.0})
    assert data_gate(f, s)["gate"] == "PASS"


def test_local_market_time_converts_to_utc():
    x = pd.Series(pd.to_datetime(["2025-01-02 09:15:00", "2025-01-02 09:16:00"]))
    y = to_utc_naive(x)
    assert str(y.iloc[0]) == "2025-01-02 03:45:00"


def test_utc_like_naive_time_is_preserved():
    x = pd.Series(pd.to_datetime(["2025-01-02 03:45:00", "2025-01-02 03:46:00"]))
    y = to_utc_naive(x)
    assert str(y.iloc[0]) == "2025-01-02 03:45:00"


# execution trigger checkpoint 2026-09-24

# v2d trigger checkpoint
