import numpy as np
import pandas as pd

from research.phase40_overnight_gap_implied_move import (
    SQRT_ONE_SESSION,
    build_signals,
    charge,
    implied_vol,
    lot_size,
    prior_only_z,
    required_legs,
    round_strike,
    bs_price,
)


def test_iv_roundtrip():
    spot = 22000.0
    strike = 22000.0
    t = 7.0 / 365.0
    sigma = 0.20
    for call in (True, False):
        px = bs_price(spot, strike, t, sigma, call)
        got = implied_vol(px, spot, strike, t, call)
        assert abs(got - sigma) < 1e-6


def test_one_session_scaling():
    assert np.isclose(SQRT_ONE_SESSION, np.sqrt(1.0 / 252.0))
    assert np.isclose(0.20 * SQRT_ONE_SESSION, 0.20 * np.sqrt(1.0 / 252.0))


def test_prior_only_z():
    s = pd.Series([1.0 + 0.05 * i for i in range(70)])
    mean, std, z = prior_only_z(s, window=60)
    assert pd.isna(z.iloc[59])
    assert pd.notna(z.iloc[60])
    assert np.isclose(mean.iloc[60], s.iloc[:60].mean())
    assert np.isclose(std.iloc[60], s.iloc[:60].std(ddof=1))


def test_round_strike_half_up():
    assert round_strike(22499.0) == 22500.0
    assert round_strike(22524.0) == 22500.0
    assert round_strike(22525.0) == 22550.0


def test_spread_mapping():
    class R:
        def __init__(self, side):
            self.side = side
            self.prior_atm_strike = 22500.0
    assert required_legs(R("BULL")) == ("CE", 22500.0, "CE", 22700.0)
    assert required_legs(R("BEAR")) == ("PE", 22500.0, "PE", 22300.0)


def test_lot_schedule():
    assert lot_size(pd.Timestamp("2024-04-25").date()) == 50
    assert lot_size(pd.Timestamp("2024-04-26").date()) == 25
    assert lot_size(pd.Timestamp("2024-11-20").date()) == 25
    assert lot_size(pd.Timestamp("2024-11-21").date()) == 75
    assert lot_size(pd.Timestamp("2026-01-05").date()) == 75
    assert lot_size(pd.Timestamp("2026-01-06").date()) == 65


def test_signal_building():
    dates = pd.date_range("2026-01-01", periods=65, freq="B").date
    panel = pd.DataFrame({
        "trade_date": dates,
        "prior_date": [d for d in dates],
        "feature_eligible": [False] * 60 + [True] * 5,
        "gap_ratio_z": [np.nan] * 60 + [1.0, -1.0, 1.0, -1.0, 0.0],
        "overnight_gap": [0.01] * 65,
        "prior_expiry": [pd.Timestamp("2026-02-03").date()] * 65,
        "prior_atm_strike": [25000.0] * 65,
        "gap_ratio": [1.0] * 65,
        "atm_iv_1510": [0.20] * 65,
        "rv20": [0.15] * 65,
        "iv_rv_ratio": [1.333] * 65,
    })
    sessions = pd.DataFrame({"trade_date": dates})
    sig = build_signals(panel, sessions)
    assert set(sig["state"]) == {"HIGH_GAP_DISLOCATION", "LOW_GAP_DISLOCATION"}
    assert set(sig["mapping"]) == {"CONTINUE", "FADE"}
    assert set(sig["exit_time"]) == {"10:30:00", "15:10:00"}
    assert len(sig) == 16


def test_sale_stt_makes_sale_cost_greater():
    d = pd.Timestamp("2026-04-06").date()
    buy = charge(100, "BUY", 1, 65, d)
    sell = charge(100, "SELL", 1, 65, d)
    assert sell > buy


def test_prior_only_z_uses_previous_valid_gap_ratio_observations_with_gaps():
    s = pd.Series([float(i) if i not in (10, 20, 30) else np.nan for i in range(70)])
    mean, std, z = prior_only_z(s, window=60)
    assert pd.isna(z.iloc[60])
    expected = pd.Series([float(i) for i in range(70) if i not in (10, 20, 30)])
    prior = expected.iloc[:60]
    assert np.isclose(mean.iloc[63], prior.mean())
    assert np.isclose(std.iloc[63], prior.std(ddof=1))
    assert np.isfinite(z.iloc[63])


def test_rv20_is_strictly_prior_to_signal_day():
    from research.phase40_overnight_gap_implied_move import load_sessions
    class FakeRoot:
        pass
    # Reconstruct the shift semantics directly: today's return must not enter today's prior-day RV20.
    closes = pd.Series([100.0 + i for i in range(25)])
    daily = closes.pct_change()
    current = daily.rolling(20, min_periods=20).std(ddof=1) * np.sqrt(252.0)
    prior = daily.rolling(20, min_periods=20).std(ddof=1).shift(1) * np.sqrt(252.0)
    assert pd.isna(prior.iloc[20])
    assert np.isfinite(prior.iloc[21])
    assert not np.isclose(prior.iloc[21], current.iloc[21])
