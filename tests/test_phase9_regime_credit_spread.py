from research.phase9_regime_credit_spread import variant_grid, EXIT_PROFILES


def test_phase9_variant_count():
    assert len(variant_grid()) == 96
    assert {v.family for v in variant_grid()} == {"BULL_PUT", "BEAR_CALL"}


def test_variant_keys_unique():
    keys = [v.key for v in variant_grid()]
    assert len(keys) == len(set(keys))


def test_exit_profiles_bounded():
    assert EXIT_PROFILES[0]["stop_mult"] < EXIT_PROFILES[1]["stop_mult"]
    assert EXIT_PROFILES[0]["target_capture"] < EXIT_PROFILES[1]["target_capture"]


def test_credit_spread_gross_direction():
    from research.cost_model import OptionCostModel
    cm = OptionCostModel()
    pnl = cm.vertical_credit_spread_net_pnl(30, 10, 15, 5, lot_size=65, slippage_points=0.0)
    assert pnl > 0
