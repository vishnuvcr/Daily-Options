import numpy as np
import pandas as pd

from research.phase39_implied_realized_opening_dislocation import (
    SQRT_SESSION,
    build_signals,
    charge,
    implied_15m_move_pct,
    implied_vol,
    lot_size,
    prior_only_z,
    required_legs,
    round_strike,
)


def test_black_scholes_iv_roundtrip_call_and_put():
    spot = 22000.0
    strike = 22000.0
    t = 7.0 / 365.0
    sigma = 0.20
    from research.phase39_implied_realized_opening_dislocation import bs_price
    for call in (True, False):
        px = bs_price(spot, strike, t, sigma, call)
        got = implied_vol(px, spot, strike, t, call)
        assert np.isfinite(got)
        assert abs(got - sigma) < 1e-6


def test_implied_move_scaling():
    assert np.isclose(implied_15m_move_pct(0.20), 0.20 * SQRT_SESSION)
    assert np.isclose(implied_15m_move_pct(0.10), 0.5 * implied_15m_move_pct(0.20))


def test_prior_only_zscore_excludes_current_observation():
    s = pd.Series([1.0 + 0.1 * i for i in range(70)])
    mean, std, z = prior_only_z(s, window=60)
    assert pd.isna(z.iloc[59])
    assert pd.notna(z.iloc[60])
    assert np.isclose(mean.iloc[60], s.iloc[:60].mean())
    assert np.isclose(std.iloc[60], s.iloc[:60].std(ddof=1))


def test_strike_rounding_is_deterministic():
    assert round_strike(22499.0) == 22500.0
    assert round_strike(22524.0) == 22500.0
    assert round_strike(22525.0) == 22550.0


def test_directional_spread_mapping():
    class R:
        def __init__(self, side):
            self.side = side
            self.atm_strike = 22500.0
    assert required_legs(R("BULL")) == ("CE", 22500.0, "CE", 22700.0)
    assert required_legs(R("BEAR")) == ("PE", 22500.0, "PE", 22300.0)


def test_lot_size_schedule_matches_frozen_cost_model():
    assert lot_size(pd.Timestamp("2024-04-25").date()) == 50
    assert lot_size(pd.Timestamp("2024-04-26").date()) == 25
    assert lot_size(pd.Timestamp("2024-11-20").date()) == 25
    assert lot_size(pd.Timestamp("2024-11-21").date()) == 75
    assert lot_size(pd.Timestamp("2026-01-05").date()) == 75
    assert lot_size(pd.Timestamp("2026-01-06").date()) == 65


def test_charge_positive_and_sale_stt_exceeds_buy_charge_for_same_price_after_stt_change():
    d = pd.Timestamp("2026-04-06").date()
    buy = charge(100.0, "BUY", 1, 65, d)
    sell = charge(100.0, "SELL", 1, 65, d)
    assert buy > 0
    assert sell > buy


def test_signal_building_uses_next_trading_day_and_frozen_cells():
    dates = pd.date_range("2026-01-01", periods=65, freq="B").date
    panel = pd.DataFrame({
        "trade_date": dates,
        "feature_eligible": [False] * 60 + [True] * 5,
        "move_ratio_z": [np.nan] * 60 + [1.0, -1.0, 1.0, -1.0, 0.0],
        "opening_return": [0.01] * 65,
        "front_expiry": [pd.Timestamp("2026-02-03").date()] * 65,
        "atm_strike": [25000.0] * 65,
        "move_ratio": [1.0] * 65,
    })
    sessions = pd.DataFrame({"trade_date": dates})
    sig = build_signals(panel, sessions)
    assert set(sig["state"]) == {"HIGH_DISLOCATION", "LOW_DISLOCATION"}
    assert set(sig["mapping"]) == {"CONTINUE", "FADE"}
    assert set(sig["exit_time"]) == {"10:30:00", "15:10:00"}
    assert len(sig) == 16
    assert (sig["trade_date"] > sig["signal_date"]).all()

    
def test_prior_only_z_uses_sixty_previous_valid_observations_when_gaps_exist():
    s = pd.Series([float(i) if i not in (10, 20, 30) else np.nan for i in range(70)])
    mean, std, z = prior_only_z(s, window=60)
    assert pd.isna(z.iloc[60])
    expected = pd.Series([float(i) for i in range(70) if i not in (10, 20, 30)])
    prior = expected.iloc[:60]
    assert np.isclose(mean.iloc[63], prior.mean())
    assert np.isclose(std.iloc[63], prior.std(ddof=1))
    assert np.isfinite(z.iloc[63])
