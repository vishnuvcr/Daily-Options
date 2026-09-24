from research.phase13b_frozen_oos import SIGNAL_TIME, Z_THRESHOLD, RV_PERCENTILE, HOLD_MINUTES

def test_frozen_rule_constants():
    assert SIGNAL_TIME == '14:45:00'
    assert Z_THRESHOLD == 1.5
    assert RV_PERCENTILE == 80.0
    assert HOLD_MINUTES == 10
# frozen-oos trigger checkpoint 2026-09-24

# acquisition-fix trigger checkpoint 2026-09-24

# parquet-layout trigger checkpoint 2026-09-24


def test_load_option_window_handles_expiry_column(tmp_path):
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    from research.phase13b_frozen_oos import load_option_window

    p = tmp_path / "sample.parquet"
    df = pd.DataFrame({
        "datetime": pd.to_datetime(["2021-01-04 09:16:00", "2021-01-04 09:17:00"]),
        "date": [pd.Timestamp("2021-01-04").date(), pd.Timestamp("2021-01-04").date()],
        "option_type": ["CALL", "CALL"],
        "expiry": ["2021-01-28", "2021-01-28"],
        "strike_price": [100.0, 100.0],
        "open": [10.0, 10.5],
        "high": [10.6, 10.8],
        "low": [9.9, 10.2],
        "close": [10.4, 10.7],
        "expiry_type": ["MONTH", "MONTH"],
        "strike_type": ["ATM", "ATM"],
    })
    df.to_parquet(p)
    out = load_option_window(str(p), ["2021-01-04"])
    assert len(out) == 2
    assert out.iloc[0]["expiry"] == pd.Timestamp("2021-01-28")
