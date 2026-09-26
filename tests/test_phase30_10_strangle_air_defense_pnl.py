from itertools import product

from research.phase30_10_strangle_air_defense_pnl import (
    ACTIONS,
    ENTRY_DAYS,
    ENTRY_TIMES,
    EXPIRY_CHOICES,
    RISKS,
    STRIKE_METHODS,
    TRIGGERS,
    bs_call_delta,
    bs_put_abs_delta,
    expected_strikes,
)


def test_matrix_size():
    assert len(list(product(
        ENTRY_DAYS, ENTRY_TIMES, EXPIRY_CHOICES, STRIKE_METHODS,
        TRIGGERS, ACTIONS, RISKS
    ))) == 720


def test_black_scholes_put_call_deltas_are_reasonable():
    spot = 25000.0
    strike = 25000.0
    sigma = 0.15
    t = 7 / 365
    c = bs_call_delta(spot, strike, sigma, t)
    p = bs_put_abs_delta(spot, strike, sigma, t)
    assert 0.45 < c < 0.55
    assert 0.45 < p < 0.55


def test_expected_sigma_strikes_are_otm():
    strikes = [24000.0, 24500.0, 25000.0, 25500.0, 26000.0]
    put_k, call_k = expected_strikes(
        25000.0, strikes, 0.15, 7 / 365, "sigma1"
    )
    assert put_k < 25000.0
    assert call_k > 25000.0


def test_expected_delta_strikes_form_strangle():
    strikes = [24000.0, 24500.0, 25000.0, 25500.0, 26000.0]
    put_k, call_k = expected_strikes(
        25000.0, strikes, 0.15, 7 / 365, "delta020"
    )
    assert put_k < call_k
