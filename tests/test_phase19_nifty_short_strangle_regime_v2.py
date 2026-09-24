from research.phase19_nifty_short_strangle_regime import variant_grid as v1_grid
from research.phase19_nifty_short_strangle_regime_v2 import variant_grid as v2_grid


def test_v2_preserves_frozen_grid():
    assert len(v1_grid()) == 144
    assert v2_grid() == v1_grid()


def test_v2_has_date_safe_vectorized_simulator():
    from research.phase19_nifty_short_strangle_regime_v2 import simulate
    assert callable(simulate)
