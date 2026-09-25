#!/usr/bin/env python3
"""Phase 29.4 deterministic source-fact extraction.

This phase does not backtest. It converts source-caption transcripts into
structured facts while avoiding plaintext transcript persistence.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from research.phase29_3_iron_dome_content import VIDEOS, fetch_transcript

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIME_PAT = re.compile(r"(?<!\d)(\d{1,2})[:.](\d{2})\s*(a\.?m\.?|p\.?m\.?)?", re.I)
PCT_PAT = re.compile(r"(?<!\d)(\d{1,3})\s*%")
POINT_PAT = re.compile(r"(?<!\d)(\d{2,4})\s*(?:points?|point)")
STRIKE_PAT = re.compile(r"(?<!\d)(\d{4,5})(?!\d)")
HOLD_PAT = re.compile(r"\b(two|three|four)\b(?:\s*,)?\s*(?:or\s*)?(?:\s*maybe\s*)?(?:four\b\s*)?days?\b", re.I)

def extract_fact_candidates(snippets: list[dict]) -> dict:
    weekdays = set()
    times = set()
    percentages = set()
    point_values = set()
    strike_like = set()
    hold_days = set()
    adjustment_terms = set()
    actions = set()

    for s in snippets:
        text = str(s.get("text", ""))
        lower = text.lower()
        for day in WEEKDAYS:
            if re.search(r"\b" + day + r"\b", text, re.I):
                weekdays.add(day)

        for m in TIME_PAT.finditer(text):
            h = int(m.group(1))
            minute = int(m.group(2))
            suffix = (m.group(3) or "").lower().replace(".", "")
            if suffix == "pm" and h < 12:
                h += 12
            if suffix == "am" and h == 12:
                h = 0
            times.add(f"{h:02d}:{minute:02d}")

        percentages.update(int(m.group(1)) for m in PCT_PAT.finditer(text))
        point_values.update(int(m.group(1)) for m in POINT_PAT.finditer(text))

        for value in STRIKE_PAT.findall(text):
            ivalue = int(value)
            if 10000 <= ivalue <= 50000 and ivalue not in (2026,):
                strike_like.add(ivalue)

        if re.search(r"\b(two|2)\b", lower) and "adjust" in lower:
            adjustment_terms.add("two_adjustments")
        if "one strike inside" in lower:
            adjustment_terms.add("one_strike_inside")
        if "more in the money" in lower or "more in money" in lower:
            adjustment_terms.add("deeper_itm_directional_roll")
        if "60% mark" in lower:
            adjustment_terms.add("60_percent_mark")

        for action in ("buy", "sell", "move", "roll", "close", "exit", "square"):
            if re.search(r"\b" + action + r"\b", lower):
                actions.add(action)

        # The source explicitly states a 2–4 day holding window.
        if re.search(r"two,\s*three,\s*maybe\s*four\s*days", lower):
            hold_days.update({2, 3, 4})

    return {
        "weekdays": sorted(weekdays),
        "times": sorted(times),
        "percentages": sorted(percentages),
        "point_values": sorted(point_values),
        "strike_like_values": sorted(strike_like),
        "hold_days": sorted(hold_days),
        "adjustment_terms": sorted(adjustment_terms),
        "actions": sorted(actions),
    }


def classify_rule_status(label: str) -> str:
    return {
        "explicit": "EXPLICIT",
        "example": "ILLUSTRATIVE",
        "formalization": "FORMALIZATION_REQUIRED",
        "unknown": "UNRESOLVED",
    }[label]


def main() -> int:
    rows = []
    for video in VIDEOS:
        snippets, language, label, generated, source = fetch_transcript(video["video_id"])
        facts = extract_fact_candidates(snippets)
        rows.append({
            "video_id": video["video_id"],
            "reference_date": video["reference_date"],
            "source": source,
            "language": language,
            "generated": generated,
            "fact_candidates": facts,
        })

    common = set(rows[0]["fact_candidates"]["adjustment_terms"]) & set(rows[1]["fact_candidates"]["adjustment_terms"])
    report = {
        "phase": "29.4",
        "videos": rows,
        "cross_video_common_adjustment_terms": sorted(common),
        "rule_ledger": [
            {"field": "underlying", "value": "NIFTY", "status": "EXPLICIT"},
            {"field": "core_structure", "value": "weekly iron-fly / short-straddle with balanced protection", "status": "EXPLICIT"},
            {"field": "illustrated_wing_width_points", "value": 200, "status": "ILLUSTRATIVE"},
            {"field": "max_adjustments", "value": 2, "status": "EXPLICIT"},
            {"field": "adjustment_trigger", "value": "60% mark", "status": "EXPLICIT"},
            {"field": "adjustment_trigger_metric", "value": None, "status": "UNRESOLVED"},
            {"field": "entry_timing_relative_to_expiry", "value": "2–4 trading sessions before expiry family", "status": "FORMALIZATION_REQUIRED"},
            {"field": "entry_clock", "value": None, "status": "UNRESOLVED"},
            {"field": "one_strike_inside", "value": "directional adjustment example", "status": "ILLUSTRATIVE"},
            {"field": "exit_anchor", "value": "15:00 on expiry day", "status": "ILLUSTRATIVE"},
            {"field": "lot_ratio", "value": "1:1:1:1", "status": "FORMALIZATION_REQUIRED"},
        ],
        "numerical_backtest_allowed": 0,
        "phase30_gate": "BLOCKED",
        "next_required": [
            "Verify historical NIFTY lot size and expiry regime at the candidate entry dates.",
            "Freeze the exact trigger metric and adjustment leg mapping.",
            "Register executable pricing and Paytm Money/NSE friction before Phase 30."
        ],
    }

    Path("reports").mkdir(exist_ok=True)
    Path("reports/phase29_4_rule_fact_candidates.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
