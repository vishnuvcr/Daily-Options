#!/usr/bin/env python3
"""Phase 29.5 deterministic Iron Dome formalization and contract gate."""
from __future__ import annotations

import itertools
import json
from datetime import date, timedelta
from pathlib import Path

VIDEOS = [
    {"video_id": "5xz7X5QsFv8", "reference_date": date(2026, 4, 30)},
    {"video_id": "9cetNfglyO4", "reference_date": date(2026, 5, 2)},
]

ENTRY_OFFSETS = (-4, -3, -2)
TRIGGERS = ("WING_60", "RISK_60")
ADJUSTMENTS = ("RECENTER_BOTH", "ONE_STRIKE_INSIDE")
WING_POINTS = 200
STRIKE_INTERVAL = 50
LOT_RATIO = (1, 1, 1, 1)


def lot_size(expiry: date) -> int:
    if expiry < date(2024, 4, 26):
        return 50
    if expiry < date(2024, 11, 21):
        return 25
    if expiry < date(2026, 1, 6):
        return 75
    return 65


def next_tuesday(d: date) -> date:
    days = (1 - d.weekday()) % 7
    return d + timedelta(days=days)


def build_matrix() -> list[dict]:
    rows = []
    for i, (entry_offset, trigger, adjustment) in enumerate(
        itertools.product(ENTRY_OFFSETS, TRIGGERS, ADJUSTMENTS), start=1
    ):
        rows.append(
            {
                "cell_id": f"ID29_5_{i:02d}",
                "entry_offset_trading_sessions": entry_offset,
                "entry_clock": "09:30",
                "trigger": trigger,
                "adjustment": adjustment,
                "max_adjustments": 2,
                "wing_points": WING_POINTS,
                "strike_interval": STRIKE_INTERVAL,
                "lot_ratio": LOT_RATIO,
                "exit_clock": "15:00",
                "expiry_day_rule": "TUESDAY_OR_PREVIOUS_TRADING_DAY",
            }
        )
    return rows


def main() -> int:
    matrix = build_matrix()
    assert len(matrix) == 12
    contract_checks = []
    for v in VIDEOS:
        expiry = next_tuesday(v["reference_date"])
        contract_checks.append(
            {
                "video_id": v["video_id"],
                "reference_date": v["reference_date"].isoformat(),
                "next_tuesday_expiry": expiry.isoformat(),
                "historical_lot_size": lot_size(expiry),
                "weekly_strike_interval": STRIKE_INTERVAL,
                "lot_size_is_2026_revision": expiry >= date(2026, 1, 6),
            }
        )
    report = {
        "phase": "29.5",
        "formalization_cells": matrix,
        "cell_count": len(matrix),
        "contract_checks": contract_checks,
        "numerical_backtest_allowed": 0,
        "phase30_gate": "BLOCKED",
        "gate_reason": [
            "All 12 cells require exact historical contract joins before P&L.",
            "Bid/ask quote completeness remains unverified; OHLC is not a spread observation.",
            "Paytm Money/NSE date-aware cost model must be frozen in Phase 30.",
        ],
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/phase29_5_formalization_matrix.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
