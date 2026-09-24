import pandas as pd

from research.phase11_breakout_pullback_oi import (
    BREAKOUT_PCTS,
    ENTRY_TIMES,
    HOLDS,
    OPENING_RANGES,
    PULLBACK_TOLS,
    RISK_PROFILES,
    variant_grid,
)


def test_phase11_variant_count():
    assert len(variant_grid()) == 64
    assert OPENING_RANGES == (5, 15)
    assert BREAKOUT_PCTS == (0.0005, 0.0010)
    assert PULLBACK_TOLS == (0.0002, 0.0005)
    assert ENTRY_TIMES == ("09:45:00", "10:00:00")
    assert HOLDS == (15, 30)
    assert len(RISK_PROFILES) == 2


def test_variant_keys_unique():
    keys = [v.key for v in variant_grid()]
    assert len(keys) == len(set(keys))


def test_oi_bias_directional():
    df = pd.DataFrame({"put_oi": [120.0], "call_oi": [80.0]})
    bias = (df["put_oi"] - df["call_oi"]) / (df["put_oi"] + df["call_oi"])
    assert float(bias.iloc[0]) > 0
