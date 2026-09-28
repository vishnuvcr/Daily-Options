import pandas as pd
import numpy as np

from research.phase38_opening_volatility_structure import (
    Z_THRESHOLD, build_feature_panel, build_signals, round_strike
)

def fixture():
    dates = pd.date_range("2026-01-01", periods=75, freq="B")
    rows=[]
    for d in dates:
        ds=d.date()
        rows += [
            {"ts":pd.Timestamp(f"{ds} 09:15:00"),"open_px":100.0,"high_px":101.0,"low_px":99.0,"close_px":100.2,"date":ds,"time":"09:15:00"},
            {"ts":pd.Timestamp(f"{ds} 09:16:00"),"open_px":100.2,"high_px":100.4,"low_px":100.0,"close_px":100.1,"date":ds,"time":"09:16:00"},
            {"ts":pd.Timestamp(f"{ds} 09:29:00"),"open_px":100.1,"high_px":102.0,"low_px":98.0,"close_px":101.0,"date":ds,"time":"09:29:00"},
            {"ts":pd.Timestamp(f"{ds} 09:30:00"),"open_px":101.0,"high_px":101.5,"low_px":100.5,"close_px":101.1,"date":ds,"time":"09:30:00"},
        ]
    return pd.DataFrame(rows)

def test_prior_only_warmup():
    p=build_feature_panel(fixture())
    eligible=p[p["feature_eligible"]]
    assert len(eligible) == len(p) - 60
    first=eligible.iloc[0]
    assert first["prior_date"] < first["date"]

def test_current_observation_is_not_in_prior_mean():
    p=build_feature_panel(fixture())
    row=p.iloc[61]
    prior = p["early_range_pct"].iloc[:61].shift(1).tail(60)
    assert np.isclose(row["prior_mean"], prior.mean(), equal_nan=False)
    assert not np.isclose(row["prior_mean"], p["early_range_pct"].iloc[61])

def test_opening_window_stops_at_0929():
    p=build_feature_panel(fixture())
    row=p.iloc[-1]
    assert np.isclose(row["early_range_pct"], (102-98)/100)

def test_signal_direction_mapping():
    p=build_feature_panel(fixture())
    p["range_z"] = Z_THRESHOLD + 0.1
    p["feature_eligible"] = True
    p["barrier_ok"] = True
    p["state"] = "HIGH_VOL"
    p["expiry"] = pd.Timestamp("2026-01-06").date()
    p["spot_0930"] = 101.1
    p["atm"] = 100
    s=build_signals(p)
    assert set(s["mapping"]) == {"CONTINUE","FADE"}
    assert (s[s["mapping"]=="CONTINUE"]["side"]=="CALL").all()
    assert (s[s["mapping"]=="FADE"]["side"]=="PUT").all()

def test_atm_rounding():
    assert round_strike(22499) == 22500
    assert round_strike(22524) == 22500
    assert round_strike(22525) == 22550
