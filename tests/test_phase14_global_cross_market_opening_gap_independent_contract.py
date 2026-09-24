import pandas as pd
from research.phase14_global_cross_market_opening_gap_independent_contract import frozen_signal_dates

def test_frozen_rule_direction():
    x = pd.DataFrame({
        "trade_date": [pd.Timestamp("2021-08-02").date()],
        "datetime": pd.to_datetime(["2021-08-02 04:00:00"]),
        "trade_time_ist": ["09:30:00"],
        "global_global3": [1.0],
        "gap_signal": [-0.01],
        "spot_close": [100.0],
    })
    y = frozen_signal_dates(x)
    assert len(y) == 1
    assert y.iloc[0]["direction"] == "CALL"
