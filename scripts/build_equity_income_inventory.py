#!/usr/bin/env python3
"""Build a deterministic, transcript-aware Equity Income channel inventory.

This phase deliberately does not infer strategy rules from transcript text.
Title-based family labels are candidate hints only and remain UNRESOLVED until
Phase 27 reconstructs the source rules from archived transcripts.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


FAMILY_RULES = (
    ("iron_condor", ("iron condor", "iron-clad", "iron dome", "air defense")),
    ("iron_fly", ("iron fly", "ironfly", "iron-fly")),
    ("calendar", ("calendar", "cross calendar")),
    ("diagonal", ("diagonal",)),
    ("ratio_spread", ("ratio spread", "ratio")),
    ("covered_call", ("covered call",)),
    ("jade_lizard", ("jade lizard",)),
    ("credit_spread", ("credit spread", "bull put", "bear call")),
    ("debit_spread", ("debit spread", "bear put", "bull call")),
    ("strangle", ("strangle",)),
    ("straddle", ("straddle",)),
    ("put_strategy", ("sold put", "put shield", "put adjustment")),
    ("pcr_directional", ("pcr",)),
    ("gamma", ("gamma",)),
    ("leaps", ("leaps",)),
    ("indicator_signal", ("indicator", "magnet", "workflow")),
    ("covered_or_equity", ("options selling", "stock options")),
)


def read_jsonl(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            out[str(item["video_id"])] = item
    return out


def normalize_title(title: str) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", (title or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def family_guess(title: str) -> str:
    t = (title or "").lower()
    matches = [name for name, needles in FAMILY_RULES if any(n in t for n in needles)]
    return "|".join(matches) if matches else "unclassified"


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("data/equity_income"))
    args = parser.parse_args()

    videos = read_jsonl(args.root / "video_manifest.jsonl")
    transcripts = read_jsonl(args.root / "transcript_manifest.jsonl")
    if not videos:
        raise SystemExit("NO_VIDEO_MANIFEST")
    if set(videos) != set(transcripts):
        raise SystemExit(f"ARCHIVE_ID_MISMATCH videos={len(videos)} transcripts={len(transcripts)}")

    duplicate_counts = Counter(normalize_title(v.get("title", "")) for v in videos.values())
    inventory_rows = []
    registry_rows = []

    for video_id, video in sorted(videos.items(), key=lambda kv: (kv[1].get("title") or "", kv[0])):
        transcript = transcripts.get(video_id, {})
        status = transcript.get("status", "missing")
        if status not in {"archived", "already_archived"}:
            raise SystemExit(f"UNRESOLVED_TRANSCRIPT:{video_id}:{status}")
        title = video.get("title") or ""
        guess = family_guess(title)
        title_key = normalize_title(title)
        duplicate_group = f"title:{title_key}" if duplicate_counts[title_key] > 1 and title_key else ""
        transcript_method = transcript.get("method", "")
        transcript_error = transcript.get("error", "")

        inventory_rows.append({
            "video_id": video_id,
            "title": title,
            "webpage_url": video.get("webpage_url", ""),
            "transcript_status": status,
            "transcript_method": transcript_method,
            "transcript_error": transcript_error,
            "transcript_integrity": "VERIFIED",
            "snippet_count": transcript.get("snippet_count", 0),
            "candidate_payoff_family": guess,
            "duplicate_title_group": duplicate_group,
            "source_fidelity": "UNRESOLVED",
            "phase_status": "PENDING",
        })

        registry_rows.append({
            "strategy_id": f"EI_VIDEO_{video_id}",
            "source_video_ids": video_id,
            "title_set": title,
            "strategy_name": title.strip() or f"Equity Income {video_id}",
            "underlying": "",
            "timeframe": "",
            "payoff_family": guess,
            "entry_rule": "",
            "strike_rule": "",
            "adjustment_rule": "",
            "stop_rule": "",
            "target_rule": "",
            "exit_rule": "",
            "capital_rule": "",
            "source_fidelity": "UNRESOLVED",
            "data_status": "UNRESOLVED",
            "duplicate_group": duplicate_group,
            "phase_status": "PENDING",
        })

    fields = list(inventory_rows[0].keys())
    write_csv(args.root / "video_inventory.csv", inventory_rows, fields)

    registry_fields = list(registry_rows[0].keys())
    write_csv(args.root / "strategy_registry.csv", registry_rows, registry_fields)

    counts = Counter(row["transcript_status"] for row in inventory_rows)
    families = Counter(
        family for row in inventory_rows for family in row["candidate_payoff_family"].split("|")
    )
    snapshot = {
        "schema_version": 1,
        "videos": len(inventory_rows),
        "transcript_status_counts": dict(sorted(counts.items())),
        "candidate_family_counts": dict(sorted(families.items())),
        "strategy_candidates": sum(1 for row in inventory_rows if row["candidate_payoff_family"] != "unclassified"),
        "transcript_verified": sum(1 for row in inventory_rows if row["transcript_status"] in {"archived", "already_archived"}),
        "phase": 26,
        "backtesting_started": False,
    }
    (args.root / "inventory_snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(snapshot, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
