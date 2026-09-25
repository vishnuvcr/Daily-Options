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