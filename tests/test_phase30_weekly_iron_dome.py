from datetime import date
from research.phase30_weekly_iron_dome import (
    WEEKLY_TARGET,
    POSITIVE_WEEK_RATE_TARGET,
    EXECUTION_COVERAGE_TARGET,
    lot_size,
    round_strike,
)

def test_weekly_gate_is_5000():
    assert WEEKLY_TARGET == 5000.0
    assert POSITIVE_WEEK_RATE_TARGET == 0.70
    assert EXECUTION_COVERAGE_TARGET == 0.80

def test_date_aware_lot_schedule():
    assert lot_size(date(2025, 12, 30)) == 75
    assert lot_size(date(2026, 1, 6)) == 65

def test_round_strike():
    assert round_strike(2499) == 2500
    assert round_strike(2501) == 2500
    assert round_strike(2526) == 2550

from research.phase30_weekly_iron_dome import STRIKE_INTERVAL

def test_one_strike_inside_moves_deeper_itm():
    ce_strike = 25000.0
    pe_strike = 25000.0
    assert ce_strike - STRIKE_INTERVAL == 24950.0
    assert pe_strike + STRIKE_INTERVAL == 25050.0

import pandas as pd
from research.phase30_weekly_iron_dome import build_mark_panel, first_trigger

def test_vectorized_wing_trigger_uses_first_crossing():
    spot = pd.DataFrame({
        "ts": pd.to_datetime(["2026-01-01 09:31:00","2026-01-01 09:32:00","2026-01-01 09:33:00"]),
        "close_px": [25000.0,25120.0,25125.0],
    })
    leg = {
        "active": True,
        "series": pd.DataFrame({
            "ts": pd.to_datetime(["2026-01-01 09:31:00","2026-01-01 09:32:00","2026-01-01 09:33:00"]),
            "close_px": [100.0,90.0,85.0],
        }),
        "position": "SHORT",
        "qty": 1,
        "lot": 65,
    }
    panel = build_mark_panel(spot,[leg],spot.ts.iloc[0],spot.ts.iloc[-1])
    hit = first_trigger(panel,[leg],"WING_60",25000.0,0.0,1000.0)
    assert hit is not None
    assert hit["ts"] == pd.Timestamp("2026-01-01 09:32:00")
    assert hit["challenged"] == "CE"


def test_option_loader_uses_full_expiry_file(tmp_path):
    import duckdb
    from research.phase30_weekly_iron_dome import load_option_series

    path = tmp_path / "2026-01-06.parquet"
    rows = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-02 09:31:00", "2026-01-05 09:31:00"]),
        "open": [100.0, 90.0],
        "close": [99.0, 89.0],
        "trading_day": pd.to_datetime(["2026-01-02", "2026-01-05"]),
        "strike": [25000.0, 25000.0],
        "option_type": ["CE", "CE"],
    })
    rows.to_parquet(path, index=False)
    con = duckdb.connect()
    series = load_option_series(con, path, date(2026, 1, 2), 25000.0, "CE", "2026-01-02 09:30:00", "2026-01-06 15:00:00")
    con.close()
    assert len(series) == 2
    assert series["ts"].dt.date.tolist() == [date(2026, 1, 2), date(2026, 1, 5)]

def test_clone_initial_legs_isolates_state():
    import research.phase30_weekly_iron_dome as mod

    series = pd.DataFrame({"ts": pd.to_datetime(["2026-01-02 09:31:00"]), "open_px": [100.0], "close_px": [99.0]})
    original = [{
        "side": "CE", "strike": 25000.0, "position": "SHORT",
        "qty": 1, "lot": 65, "entry_price": 100.0,
        "series": series, "active": True,
    }]
    cloned = mod.clone_initial_legs(original)
    cloned[0]["active"] = False
    cloned[0]["exit_price"] = 95.0

    assert original[0]["active"] is True
    assert "exit_price" not in original[0]
    assert cloned[0]["series"] is original[0]["series"]

def test_run_cell_does_not_mutate_setup_legs(monkeypatch):
    import research.phase30_weekly_iron_dome as mod

    series = pd.DataFrame({"ts": pd.to_datetime(["2026-01-02 09:31:00"]), "open_px": [100.0], "close_px": [99.0]})
    legs = [{
        "side": side, "strike": strike, "position": position, "qty": 1, "lot": 65,
        "entry_price": 100.0, "series": series, "active": True
    } for side, strike, position in [
        ("CE", 25000.0, "SHORT"),
        ("PE", 25000.0, "SHORT"),
        ("CE", 25200.0, "LONG"),
        ("PE", 24800.0, "LONG"),
    ]]
    setup = {
        "initial_legs": legs, "fill_ts": pd.Timestamp("2026-01-02 09:31:00"),
        "expiry": date(2026, 1, 6), "entry_date": date(2026, 1, 2),
        "entry_offset": -2, "lot": 65, "initial_center": 25000.0,
        "end_ts": "2026-01-06 15:31:00",
    }

    def fake_open(trade, active, exec_ts, slippage):
        trade["opened"] = trade.get("opened", 0) + len(active)

    def fake_close(trade, leg, ts, slippage):
        trade["closed"] = trade.get("closed", 0) + 1
        leg["active"] = False
        return True

    monkeypatch.setattr(mod, "open_active_structure", fake_open)
    monkeypatch.setattr(mod, "close_leg", fake_close)
    monkeypatch.setattr(mod, "cycle_anchor", lambda trade, active: 0.0)
    monkeypatch.setattr(mod, "max_loss_inr", lambda active: 1000.0)
    monkeypatch.setattr(mod, "first_trigger", lambda *args, **kwargs: None)

    empty = pd.DataFrame(columns=["ts", "spot"])
    first = mod.run_cell(None, setup, "RISK_60", "RECENTER_BOTH", 0.20, initial_panel=empty)
    second = mod.run_cell(None, setup, "RISK_60", "RECENTER_BOTH", 0.20, initial_panel=empty)

    assert first is not None and second is not None
    assert all(leg["active"] is True for leg in setup["initial_legs"])