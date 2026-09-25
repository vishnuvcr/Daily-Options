#!/usr/bin/env python3
from __future__ import annotations

import csv
from itertools import product
from pathlib import Path

ENTRY = [
    ("WED_0930", "Wednesday 09:30"),
    ("THU_0930", "Thursday 09:30"),
    ("FRI_0930", "Friday 09:30"),
]
TRIGGER = [
    ("ZONE_60", "Adverse move reaches 60% of 200-point wing distance"),
    ("PNL_60", "Open loss reaches 60% of static maximum loss"),
]
ADJUST = [
    ("ROLL_CENTER_1_STRIKE", "Move short straddle centre one strike in adverse direction"),
    ("ROLL_CENTER_2_STRIKES", "Move short straddle centre two strikes"),
    ("SHIFT_THREATENED_LONG_1_STRIKE", "Move threatened long hedge one strike inward"),
]
EXIT = [
    ("EXPIRY_15", "Close 15:00 on Tuesday expiry"),
    ("RECOVER_FLAT", "Close at post-adjustment mark-to-market >= 0, else expiry"),
]


def main() -> int:
    rows = []
    idx = 1
    for entry, trigger, adjust, exit_rule in product(ENTRY, TRIGGER, ADJUST, EXIT):
        rows.append({
            "variant_id": f"ID{idx:02d}",
            "family": "NIFTY_IRON_DOME",
            "entry_code": entry[0],
            "entry_description": entry[1],
            "trigger_code": trigger[0],
            "trigger_description": trigger[1],
            "adjustment_code": adjust[0],
            "adjustment_description": adjust[1],
            "exit_code": exit_rule[0],
            "exit_description": exit_rule[1],
            "wing_width_points": 200,
            "max_adjustments": 2,
            "expiry_regime": "CURRENT_NIFTY_WEEKLY_TUESDAY",
            "unit": "1_NIFTY_LOT",
            "execution_model": "DEFERRED_TO_PHASE30_PREREGISTERED",
            "source_fidelity": "PROVISIONAL_INTERPRETATION",
            "pnl_allowed": "NO",
        })
        idx += 1

    out = Path("reports/phase29_4_iron_dome_variant_matrix.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    assert len(rows) == 36
    assert len({r["variant_id"] for r in rows}) == 36
    assert all(r["pnl_allowed"] == "NO" for r in rows)

    summary = {
        "variant_count": len(rows),
        "entry_variants": len(ENTRY),
        "trigger_variants": len(TRIGGER),
        "adjustment_variants": len(ADJUST),
        "exit_variants": len(EXIT),
        "pnl_allowed": 0,
        "selection_rule": "NONE",
        "phase30_gate": "READY_FOR_FROZEN_VARIANT_BACKTEST",
    }
    Path("reports/phase29_4_summary.json").write_text(
        __import__("json").dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
