#!/usr/bin/env python3
from __future__ import annotations
import json
from datetime import date
from pathlib import Path

LOT_CUTOFF = date(2026, 1, 6)

def lot_size(expiry: date) -> int:
    return 75 if expiry < LOT_CUTOFF else 65

def main():
    source = {
        "current_expiry_day": "Tuesday",
        "research_window": ["2025-09-01", "2026-08-31"],
        "lot_schedule": {
            "through_2025-12-30": 75,
            "from_2026-01-06": 65,
        },
        "data_source": "rissin/nse-options-intraday",
        "intraday_granularity": "1min",
        "backtest_authorized": False,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/phase30_4_bear_put_contract_feasibility.json").write_text(
        json.dumps(source, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(source, indent=2))

if __name__ == "__main__":
    main()
