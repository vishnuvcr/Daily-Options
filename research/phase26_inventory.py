#!/usr/bin/env python3
"""Phase 26 deterministic Equity Income channel inventory.

This phase performs no backtest. It joins the archived video/transcript manifests,
flags likely strategy-bearing videos from titles, assigns a canonical payoff-family
hint, and groups near-duplicate titles. Full rule reconstruction is deliberately
deferred to Phase 27 because title heuristics are not treated as source truth.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

FAMILY_PATTERNS = [
    ("iron_condor", [r"iron[ -]?condor", r"condor"]),
    ("strangle", [r"strangle"]),
    ("straddle", [r"straddle"]),
    ("ratio_spread", [r"ratio", r"ratio[- ]?(spread|diagonal)"]),
    ("calendar_diagonal", [r"calendar", r"diagonal"]),
    ("jade_lizard", [r"jade[ -]?lizard"]),
    ("butterfly", [r"butterfly", r"iron fly", r"iron[- ]?fly"]),
    ("credit_spread", [r"credit spread", r"bull put", r"bear call", r"put spread", r"call spread"]),
    ("debit_spread", [r"debit spread", r"bull call", r"bear put"]),
    ("option_selling", [r"option selling", r"selling options", r"sell options", r"short option"]),
    ("option_buying", [r"option buyer", r"options buyer", r"buying options", r"buy options"]),
    ("hedged_income", [r"hedge", r"hedging", r"protected", r"insurance"]),
    ("leaps", [r"leaps"]),
]

STRATEGY_HINT_TERMS = {
    "strategy", "strangle", "straddle", "condor", "spread", "calendar",
    "diagonal", "ratio", "butterfly", "lizard", "selling", "sell",
    "buy", "buyer", "hedge", "hedging", "expiry", "weekly", "income",
    "payoff", "adjust", "adjustment", "trap", "setup", "trade", "trading",
    "options", "option",
}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def norm_title(title: str) -> str:
    text = re.sub(r"[^ws]", " ", title.lower())
    return re.sub(r"s+", " ", text).strip()


def family_hint(title: str) -> str:
    text = title.lower()
    matches = []
    for family, patterns in FAMILY_PATTERNS:
        score = sum(1 for pattern in patterns if re.search(pattern, text))
        if score:
            matches.append((score, family))
    if not matches:
        return "unclassified_option"
    matches.sort(key=lambda x: (-x[0], x[1]))
    return matches[0][1]


def candidate_score(title: str) -> int:
    tokens = set(norm_title(title).split())
    return sum(1 for token in tokens if token in STRATEGY_HINT_TERMS)


def duplicate_group(rows: list[dict]) -> dict[str, str]:
    groups: dict[str, str] = {}
    canonical_titles: list[tuple[str, str]] = []
    for row in sorted(rows, key=lambda x: x["video_id"]):
        title = norm_title(row.get("title") or "")
        assigned = None
        for group_id, canonical in canonical_titles:
            ratio = SequenceMatcher(None, title, canonical).ratio()
            if ratio >= 0.88:
                assigned = group_id
                break
        if assigned is None:
            assigned = f"VTG{len(canonical_titles)+1:03d}"
            canonical_titles.append((assigned, title))
        groups[row["video_id"]] = assigned
    return groups


def build_rows(video_rows: list[dict], transcript_rows: list[dict]) -> list[dict]:
    tx = {r["video_id"]: r for r in transcript_rows}
    dupes = duplicate_group(video_rows)
    out = []
    for v in sorted(video_rows, key=lambda x: (x.get("title") or "").lower()):
        tid = v["video_id"]
        t = tx.get(tid, {})
        score = candidate_score(v.get("title") or "")
        candidate = score >= 1
        out.append({
            "strategy_id": f"EI-{tid}",
            "video_id": tid,
            "title": v.get("title") or "",
            "webpage_url": v.get("webpage_url") or "",
            "candidate_score": score,
            "strategy_candidate": "YES" if candidate else "NO",
            "payoff_family_hint": family_hint(v.get("title") or ""),
            "duplicate_group": dupes[tid],
            "transcript_status": t.get("status", "MISSING"),
            "transcript_method": t.get("method", ""),
            "transcript_snippets": t.get("snippet_count", 0),
            "transcript_integrity": "VERIFIED" if t.get("status") in {"archived", "already_archived"} else "UNVERIFIED",
            "source_fidelity": "UNSPECIFIED",
            "data_status": "UNRESOLVED",
            "phase_status": "PENDING",
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data/equity_income"))
    parser.add_argument("--output", type=Path, default=Path("data/equity_income/strategy_registry.csv"))
    args = parser.parse_args()

    videos = load_jsonl(args.data_root / "video_manifest.jsonl")
    transcripts = load_jsonl(args.data_root / "transcript_manifest.jsonl")
    if len(videos) != len(transcripts):
        raise SystemExit(f"inventory mismatch: videos={len(videos)} transcripts={len(transcripts)}")

    rows = build_rows(videos, transcripts)
    if not rows:
        raise SystemExit("empty inventory")
    if any(r["transcript_integrity"] != "VERIFIED" for r in rows):
        raise SystemExit("Phase 26 requires every transcript manifest row to be integrity-verified")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "videos": len(rows),
        "transcript_verified": sum(r["transcript_integrity"] == "VERIFIED" for r in rows),
        "strategy_candidates": sum(r["strategy_candidate"] == "YES" for r in rows),
        "duplicate_groups": len({r["duplicate_group"] for r in rows}),
        "family_hints": {f: sum(r["payoff_family_hint"] == f for r in rows) for f in sorted({r["payoff_family_hint"] for r in rows})},
    }
    summary_path = args.output.with_name("phase26_inventory_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
