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
