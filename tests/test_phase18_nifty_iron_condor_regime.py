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
    assert "trades.short_offset==v.short_offset" in src
    assert "trades.wing_width==v.wing_width" in src

def test_cost_model_uses_four_leg_defined_pnl():
    src=inspect.getsource(mod.simulate)
    assert "four_leg_defined_net_pnl" in src
