from pathlib import Path
import inspect
from research.phase17_nifty_exact_expiry_premium_skew import variant_grid, expiry_for_day

def test_variant_count():
    assert len(variant_grid()) == 384

def test_expiry_selection():
    files=[(Path("2025-01-02.parquet").stem,"/x")]
    pairs=[(__import__("datetime").date(2025,1,2),Path("/x"))]
    assert expiry_for_day(pairs,__import__("datetime").date(2025,1,1))[0].isoformat()=="2025-01-02"

def test_variant_dimensions_are_frozen():
    fields=set(variant_grid()[0])
    assert {"entry_time","skew","jump","rv","width","hold","stop","side"} <= fields

def test_active_day_target_metric_in_source():
    src=inspect.getsource(__import__("research.phase17_nifty_exact_expiry_premium_skew",fromlist=["run"]))
    assert "mean_active_day_net" in src
    assert ">=1000" in src

    
def test_simulation_uses_entry_timestamp_window_and_entry_premium():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    import inspect
    src=inspect.getsource(mod.simulate)
    assert "l.entry_ts" in src
    assert "float(r.short_entry)" in src
    assert "float(r.wing_entry)" in src

def test_spot_features_do_not_nest_window_functions():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    import inspect
    src=inspect.getsource(mod.load_spot)
    assert "STDDEV_SAMP(ret1) OVER" in src
    assert "AVG(rv20) OVER" in src

    
def test_internal_direction_maps_to_source_option_codes():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    import inspect
    src=inspect.getsource(mod.build_setups)
    assert 'option_code="PE" if side=="PUT" else "CE"' in src


def test_option_quote_query_uses_close_px():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    import inspect
    src=inspect.getsource(mod.load_option_quotes)
    assert "close_px" in src
    assert "CAST(o.close AS DOUBLE) close," not in src

    
def test_build_setups_uses_next_minute_open_prices():
    import datetime as dt
    import pandas as pd
    from research.phase17_nifty_exact_expiry_premium_skew import build_setups

    ts=pd.Timestamp("2021-05-27 14:30:00",tz="Asia/Kolkata")
    et=ts+pd.Timedelta(minutes=1)
    spot=pd.DataFrame([{
        "trade_date":dt.date(2021,5,27),
        "ts":ts,
        "close":15000.0,
        "ret10":0.001,
        "rv_ratio":1.10,
    }])
    rows=[]
    strikes=[14800,14850,14900,14950,15000,15050,15100,15150,15200]
    for tstamp in [ts,et]:
        for strike in strikes:
            for code in ["PE","CE"]:
                base=100.0 if tstamp==ts else 10.0
                rows.append({
                    "ts":tstamp,
                    "trade_date":dt.date(2021,5,27),
                    "strike":strike,
                    "option_type":code,
                    "open_px":base + (15100-strike)*0.01 if code=="CE" else base + (strike-14900)*0.01,
                    "close_px":50.0,
                    "volume":1000.0,
                    "oi":2000.0,
                    "expiry":dt.date(2021,5,27),
                })
    quotes=pd.DataFrame(rows)
    setups=build_setups(spot,quotes)
    assert not setups.empty
    assert (setups.short_entry != 50.0).all()
    assert (setups.wing_entry != 50.0).all()
    assert (setups.entry_ts == et).all()


def test_timezone_aware_option_timestamp_is_preserved():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    import inspect
    src=inspect.getsource(mod.load_option_quotes)
    assert 'o."timestamp" AS ts' in src
    assert 'CAST(o.timestamp AS TIMESTAMP)' not in src
    assert 'o."timestamp"=w.ts' in src


def test_simulation_maps_internal_side_to_source_code_and_holds():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    import inspect
    src=inspect.getsource(mod.simulate)
    assert 'o.option_type=(CASE WHEN l.side=\'PUT\' THEN \'PE\' ELSE \'CE\' END)' in src
    assert 'win.hold==v["hold"]' not in src or 'trades.hold==v.hold' in inspect.getsource(mod.run)
    assert 'float(r.entry_credit)*stop' in src

    
def test_ist_timestamp_normalization_removes_timezone_at_dataframe_boundary():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    import inspect
    src=inspect.getsource(mod.ist_ts)
    assert 'tz_convert("Asia/Kolkata")' in src
    assert 'tz_localize(None)' in src

    
def test_simulation_uses_setup_id_grouping():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    import inspect
    src=inspect.getsource(mod.simulate)
    assert 'setup_df["setup_id"]' in src
    assert 'win.groupby("setup_id"' in src
    assert 'CAST(o."timestamp" AS TIMESTAMP)>=l.entry_ts' in src
