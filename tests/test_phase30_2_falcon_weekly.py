import pandas as pd
from datetime import date

from research.phase30_2_falcon_weekly import frame_series, lot_size, variant_grid, normalize_source_timestamps


def test_variant_grid_is_frozen_270():
    assert len(variant_grid()) == 270


def test_current_lot_schedule():
    assert lot_size(date(2025, 12, 30)) == 75
    assert lot_size(date(2026, 1, 6)) == 65


def test_frame_series_filters_exact_leg_without_rescan():
    frame = pd.DataFrame(
        [
            {"ts": pd.Timestamp("2025-09-03 09:31:00"), "expiry": date(2025, 9, 9),
             "strike": 25000.0, "option_type": "CE", "open_px": 100.0, "close_px": 101.0},
            {"ts": pd.Timestamp("2025-09-03 09:32:00"), "expiry": date(2025, 9, 9),
             "strike": 25000.0, "option_type": "CE", "open_px": 101.0, "close_px": 102.0},
            {"ts": pd.Timestamp("2025-09-03 09:31:00"), "expiry": date(2025, 9, 9),
             "strike": 25050.0, "option_type": "CE", "open_px": 90.0, "close_px": 91.0},
            {"ts": pd.Timestamp("2025-09-03 09:31:00"), "expiry": date(2025, 9, 9),
             "strike": 25000.0, "option_type": "PE", "open_px": 95.0, "close_px": 96.0},
        ]
    )
    out = frame_series(frame, date(2025, 9, 3), date(2025, 9, 3), 25000.0, "CE")
    assert len(out) == 2
    assert out["open_px"].tolist() == [100.0, 101.0]


def test_timestamp_normalization_handles_naive_ist_and_offset_ist():
    out = normalize_source_timestamps(pd.Series([
        "2025-09-03 09:30:00",
        "2025-09-03 09:30:00+05:30",
    ]))
    assert out.iloc[0] == pd.Timestamp("2025-09-03 09:30:00")
    assert out.iloc[1] == pd.Timestamp("2025-09-03 09:30:00")


def test_select_target_accepts_duckdb_date_and_pandas_datetime_expiry_types():
    from research.phase30_2_falcon_weekly import select_target

    frame = pd.DataFrame([
        {"expiry": pd.Timestamp("2025-09-09"), "strike": 25000.0, "option_type": "CE", "close_px": 20.2},
        {"expiry": pd.Timestamp("2025-09-09"), "strike": 25050.0, "option_type": "CE", "close_px": 21.0},
    ])
    row = select_target(frame, date(2025, 9, 9), "CE", 20.0)
    assert row is not None
    assert float(row.strike) == 25000.0

    frame["expiry"] = [date(2025, 9, 9), date(2025, 9, 9)]
    row = select_target(frame, date(2025, 9, 9), "CE", 20.0)
    assert row is not None
    assert float(row.strike) == 25000.0
