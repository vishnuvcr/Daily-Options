#!/usr/bin/env python3
"""Deterministic source-evidence extractor for Phase 30.8.

This script reads the Python-generated transcript evidence already stored in the
repository. It does not call a language model and does not infer missing rules.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# Phase-30.8 rerun checkpoint: deterministic evidence inputs are pinned on this branch.
VIDEO_ID = "OvaJumYancs"
TITLE = "No More Straddles. This Strategy Is Smarter"


def load_record(path: Path) -> dict[str, Any]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("video_id") == VIDEO_ID:
            return row
    raise RuntimeError(f"{VIDEO_ID} not found in {path}")


def collect_primary_evidence(root: Path) -> dict[str, Any]:
    clean = load_record(root / "data/equity_income/phase27_4_t1_clean_evidence.jsonl")
    full = load_record(root / "data/equity_income/phase27_1_rule_evidence.jsonl")
    return {
        "video_id": VIDEO_ID,
        "title": TITLE,
        "primary_evidence_files": [
            "data/equity_income/phase27_1_rule_evidence.jsonl",
            "data/equity_income/phase27_4_t1_clean_evidence.jsonl",
        ],
        "source_fields": {
            "underlying": full.get("fields", {}).get("underlying", []),
            "entry_action": full.get("fields", {}).get("entry_action", []),
            "strike_reference_full": full.get("fields", {}).get("strike_reference", []),
            "strike_reference_clean": clean.get("fields", {}).get("strike_reference", []),
            "width_reference": full.get("fields", {}).get("width_reference", []),
            "time_reference": full.get("fields", {}).get("time_reference", []),
            "adjustment_action": full.get("fields", {}).get("adjustment_action", []),
            "lot_reference": full.get("fields", {}).get("lot_reference", []),
        },
        "field_status_full": full.get("field_status", {}),
        "field_status_clean": clean.get("field_status", {}),
        "requires_manual_review": bool(full.get("requires_manual_review", True)),
        "source_url": full.get("source_url"),
        "retrieved_at_utc": full.get("retrieved_at_utc"),
    }


def summarize(record: dict[str, Any]) -> dict[str, Any]:
    status = record["field_status_full"]
    unresolved = [
        field for field in (
            "entry_day",
            "entry_time",
            "expiry_reference",
            "stop_reference",
            "target_reference",
            "exit_day",
            "adjustment_day",
            "delta_reference",
            "capital_reference",
        )
        if status.get(field) in {"UNSPECIFIED", None}
    ]
    return {
        "video_id": VIDEO_ID,
        "title": TITLE,
        "resolution_state": "BLOCKED_FOR_PNL",
        "source_explicit": {
            "underlying": status.get("underlying"),
            "entry_action": status.get("entry_action"),
            "width_reference": status.get("width_reference"),
            "time_reference": status.get("time_reference"),
            "adjustment_action": status.get("adjustment_action"),
            "lot_reference": status.get("lot_reference"),
        },
        "conflicts_requiring_resolution": {
            "strike_reference": status.get("strike_reference"),
            "entry_action_context": status.get("entry_action"),
            "ratio_vs_time_ambiguity": {
                "ratio_reference": status.get("ratio_reference"),
                "time_reference": status.get("time_reference"),
                "note": "The extracted '3:30' occurrences must be reconciled from transcript context before numerical use.",
            },
        },
        "unresolved_fields": unresolved,
        "no_pnl_authorization": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = collect_primary_evidence(args.root)
    payload = {
        "phase": "30.8",
        "candidate": summarize(record),
        "evidence": record,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
