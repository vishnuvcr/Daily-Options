import pandas as pd

from research.phase12_derivative_lead_options import build_nearest_contract, data_gate


def test_nearest_contract_is_expiry_aware():
    df = pd.DataFrame({
        "datetime": pd.to_datetime(["2025-01-10 09:30:00"] * 2),
        "close": [100.0, 101.0],
        "contract_month_key": [202501, 202502],
    })
    out = build_nearest_contract(df)
    assert int(out.iloc[0]["contract_month_key"]) == 202501


def test_data_gate_passes_reasonable_overlap():
    dt = pd.date_range("2025-01-01", periods=400, freq="D")
    f = pd.DataFrame({"datetime": dt, "close": 100.0, "expiry": pd.Timestamp("2026-01-01")})
    s = pd.DataFrame({"datetime": dt, "spot_close": 100.0})
    g = data_gate(f, s)
    assert g["gate"] == "PASS"
