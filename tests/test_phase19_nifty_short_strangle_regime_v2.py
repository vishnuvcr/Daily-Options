import inspect

import pandas as pd

from research.cost_model import OptionCostModel
from research.phase19_nifty_short_strangle_regime import variant_grid as v1_grid
from research.phase19_nifty_short_strangle_regime_v2 import (
    _vectorized_net_pnl,
    simulate,
    variant_grid as v2_grid,
)


def test_v2_preserves_frozen_grid():
    assert len(v1_grid()) == 144
    assert v2_grid() == v1_grid()


def test_v2_has_date_safe_vectorized_simulator():
    source = inspect.getsource(simulate)
    assert 'CAST(CAST(o."timestamp" AS TIMESTAMP) AS DATE)' in source
    assert "short_offset" in source


def test_v2_vectorized_cost_model_matches_authoritative_model():
    sample = pd.DataFrame(
        [{
            "put_entry": 100.0,
            "call_entry": 90.0,
            "put_exit": 70.0,
            "call_exit": 60.0,
            "lot_size": 65,
        }]
    )
    got = float(_vectorized_net_pnl(sample, 0.40).iloc[0])
    expected = OptionCostModel().short_strangle_net_pnl(
        100.0, 90.0, 70.0, 60.0, 65, slippage_points=0.40
    )
    assert abs(got - expected) < 1e-9
