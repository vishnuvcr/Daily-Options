from research import phase18_nifty_iron_condor_regime as mod
import inspect

def test_variant_grid_count():
    assert len(mod.variant_grid()) == 192

def test_setup_carries_structure_dimensions():
    src=inspect.getsource(mod.build_setups)
    assert '"short_offset":so' in src
    assert '"wing_width":ww' in src

def test_filter_locks_structure_dimensions():
    src=inspect.getsource(mod.filter_setups)
    assert 'setups.short_offset==v["short_offset"]' in src
    assert 'setups.wing_width==v["wing_width"]' in src

def test_variant_attribution_locks_structure_dimensions():
    src=inspect.getsource(mod.run)
    assert "short_offset" in src
    assert "wing_width" in src

def test_cost_model_uses_four_leg_defined_pnl():
    src=inspect.getsource(mod.simulate)
    assert "four_leg_defined_net_pnl" in src


def test_spot_query_uses_spot_close_alias():
    from research import phase18_nifty_iron_condor_regime as mod
    import inspect
    src=inspect.getsource(mod.load_spot)
    assert 'SELECT trade_date,ts,spot_close,ret10,rv_ratio' in src


def test_empty_setup_frame_is_non_error():
    import pandas as pd
    assert mod.filter_setups(pd.DataFrame()) .empty
