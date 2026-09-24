from research.phase8_hybrid_momentum import variant_grid, RISK_PROFILES


def test_phase8_variant_count():
    assert len(variant_grid()) == 96
    assert len(RISK_PROFILES) == 2
    assert {v.family for v in variant_grid()} == {"trend", "mean_reversion"}


def test_variant_keys_unique():
    keys = [v.key for v in variant_grid()]
    assert len(keys) == len(set(keys))


def test_risk_profiles_are_bounded():
    assert RISK_PROFILES[0]["sl_pct"] < RISK_PROFILES[1]["sl_pct"]
    assert RISK_PROFILES[0]["target_pct"] < RISK_PROFILES[1]["target_pct"]


def test_walk_forward_empty_gate():
    from research.phase8_hybrid_momentum import walk_forward
    import pandas as pd
    wf, summary = walk_forward(pd.DataFrame())
    assert wf.empty
    assert summary["gate"] == "NO_TRADES"
