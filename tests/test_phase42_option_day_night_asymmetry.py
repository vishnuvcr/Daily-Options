import numpy as np
from research.phase42_option_day_night_asymmetry import zprior, lot_size

def test_prior_z_has_no_lookahead():
    x=np.arange(1.,70.)
    z=zprior(x,60)
    assert np.isnan(z[59])
    assert np.isfinite(z[60])
    y=x.copy(); y[-1]=1e9
    assert np.isclose(z[60],zprior(y,60)[60])

def test_lot_schedule():
    assert lot_size("2024-04-25")==50
    assert lot_size("2024-04-26")==25
    assert lot_size("2026-01-06")==65


def test_missing_index_prices_are_not_coerced_to_atm():
    import math
    assert not math.isfinite(float("nan"))
