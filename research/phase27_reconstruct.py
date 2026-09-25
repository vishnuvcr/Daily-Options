#!/usr/bin/env python3
"""Phase 27 deterministic source-rule evidence extractor.

Fetches source captions with a Python HTTP client, keeps transcript text in memory
only, and writes structured rule evidence instead of plaintext transcript text.
This is a reconstruction aid, not a backtest and not an LLM transcription step.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests

DAY_RE = r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
TIME_RE = r"\b(?:[01]?\d|2[0-3])(?::[0-5]\d)(?:\s?(?:am|pm))?\b"
MONEY_RE = r"(?:₹|rs\.?|rupees?)\s*\d+(?:[,.]\d+)?"
NUMBER_RE = r"\b\d+(?:\.\d+)?\b"

FIELD_PATTERNS = {
    "entry_day": [rf"\b(?:enter|entry|start|initiat)[^\.\n]{{0,80}}({DAY_RE})", rf"({DAY_RE})[^\.\n]{{0,60}}(?:enter|entry)"],
    "adjustment_day": [rf"\b(?:adjust|adjustment|hedge|roll)[^\.\n]{{0,80}}({DAY_RE})", rf"({DAY_RE})[^\.\n]{{0,60}}(?:adjust|hedge|roll)"],
    "exit_day": [rf"\b(?:exit|close|square off|book profit)[^\.\n]{{0,80}}({DAY_RE})", rf"({DAY_RE})[^\.\n]{{0,60}}(?:exit|close|square)"],
    "underlying": [r"\b(nifty(?:\s*50)?|banknifty|sensex)\b"],
    "premium_zone": [rf"(?:premium|credit|collect|zone)[^\.\n]{{0,70}}({MONEY_RE}|\d+(?:\.\d+)?\s*points?)"],
    "time_reference": [TIME_RE],
    "expiry_reference": [r"\b(?:expiry|expiration)[^\.\n]{0,50}(monday|tuesday|wednesday|thursday|friday)\b", r"\b(monday|tuesday|wednesday|thursday|friday)[^\.\n]{0,50}\b(?:expiry|expiration)"],
    "lot_reference": [r"\b(\d+)\s*(?:lots?|lot equivalents?)\b", r"\b(\d+):(\d+)\b"],
    "strike_reference": [
        r"\b(?:atm|at the money|otm|out of the money|itm|in the money)\b",
        r"\b(?:one|two|three|four|five|\d+)\s*(?:strike|strikes?)\b",
        r"\b(?:same strike|different strike|independent strikes?|premium matched)\b",
    ],
    "stop_reference": [
        r"\b(?:stop loss|hard stop|soft stop|stop)[^\.\n]{0,90}",
        r"\b(?:exit|close)[^\.\n]{0,70}\b(?:loss|drawdown|credit)\b",
    ],
    "target_reference": [
        r"\b(?:target|profit target|book profit|take profit)[^\.\n]{0,90}",
        rf"\b(?:capture|make|earn)[^\.\n]{{0,60}}({MONEY_RE}|\d+(?:\.\d+)?\s*points?)",
    ],
}

STRATEGY_TERMS = {
    "iron_condor": ["iron condor", "condor"],
    "iron_fly": ["iron fly", "ironfly", "iron-fly"],
    "strangle": ["strangle"],
    "straddle": ["straddle"],
    "ratio_spread": ["ratio spread", "ratio", "5:3"],
    "calendar": ["calendar", "cross calendar"],
    "diagonal": ["diagonal"],
    "jade_lizard": ["jade lizard"],
    "covered_call": ["covered call"],
    "credit_spread": ["credit spread", "bull put", "bear call"],
    "debit_spread": ["debit spread", "bear put", "bull call"],
    "leaps": ["leaps"],
    "hedged_income": ["hedge", "hedged", "insurance"],
    "option_selling": ["option selling", "premium selling", "sell options"],
    "option_buying": ["option buying", "buy options", "option buyer"],
}


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def fetch_json(video_id: str, timeout=(5, 20)) -> dict:
    url = "https://youtubegpt.ai/api/transcript"
    response = requests.get(
        url,
        params={"v": video_id, "format": "json", "lang": "en"},
        headers={"User-Agent": "Daily-Options-Phase27/1.0"},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(str(data.get("message") or data.get("code") or "API_NOT_OK"))
    return data


def transcript_text(data: dict) -> str:
    return " ".join(seg.get("text", "") for seg in data.get("segments") or [] if isinstance(seg, dict))


def evidence(field: str, text: str) -> list[str]:
    out = []
    for pat in FIELD_PATTERNS[field]:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            value = (m.group(1) if m.lastindex else m.group(0)).strip()
            value = re.sub(r"\s+", " ", value)
            if value and value not in out:
                out.append(value[:200])
    return out[:12]


def family_hits(text: str) -> list[str]:
    low = norm(text)
    return [family for family, terms in STRATEGY_TERMS.items() if any(term in low for term in terms)]


def build_record(video: dict, data: dict) -> dict:
    text = transcript_text(data)
    low = norm(text)
    record = {
        "video_id": video["video_id"],
        "title": video.get("title", ""),
        "source_url": video.get("webpage_url", ""),
        "transcript_method": "youtubegpt-json",
        "segment_count": len(data.get("segments") or []),
        "transcript_character_count": len(text),
        "family_hits": family_hits(text),
        "fields": {},
        "field_status": {},
        "source_fidelity": "SOURCE-EXPLICIT" if text else "UNSPECIFIED",
        "requires_manual_review": False,
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    for field in FIELD_PATTERNS:
        vals = evidence(field, text)
        record["fields"][field] = vals
        record["field_status"][field] = "SOURCE-EXPLICIT" if vals else "UNSPECIFIED"
    material = ("entry_day", "adjustment_day", "exit_day", "strike_reference", "stop_reference", "target_reference")
    record["requires_manual_review"] = any(not record["fields"][f] for f in material)
    return record


def load_jsonl(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            out[item["video_id"]] = item
    return out


def write_jsonl(path: Path, rows: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for key in sorted(rows):
            fh.write(json.dumps(rows[key], ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, default=Path("data/equity_income/video_inventory.csv"))
    parser.add_argument("--out", type=Path, default=Path("data/equity_income/phase27_rule_evidence.jsonl"))
    parser.add_argument("--max", type=int, default=0)
    args = parser.parse_args()

    import csv
    with args.inventory.open(encoding="utf-8", newline="") as fh:
        videos = list(csv.DictReader(fh))

    candidates = [v for v in videos if v.get("candidate_payoff_family") != "unclassified"]
    if args.max:
        candidates = candidates[:args.max]

    existing = load_jsonl(args.out)
    for video in candidates:
        if video["video_id"] in existing:
            continue
        try:
            data = fetch_json(video["video_id"])
            existing[video["video_id"]] = build_record(video, data)
        except Exception as exc:
            existing[video["video_id"]] = {
                "video_id": video["video_id"],
                "title": video.get("title", ""),
                "source_url": video.get("webpage_url", ""),
                "status": "ERROR",
                "error": repr(exc),
                "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        write_jsonl(args.out, existing)

    good = [r for r in existing.values() if r.get("status") != "ERROR"]
    summary = {
        "candidate_videos": len(candidates),
        "processed": len(good),
        "errors": sum(r.get("status") == "ERROR" for r in existing.values()),
        "manual_review_required": sum(bool(r.get("requires_manual_review")) for r in good),
        "family_hit_counts": {},
    }
    for row in good:
        for family in row.get("family_hits") or []:
            summary["family_hit_counts"][family] = summary["family_hit_counts"].get(family, 0) + 1
    rules_root = Path("docs/equity_income_strategy_rules")
    rules_root.mkdir(parents=True, exist_ok=True)
    for row in good:
        if row.get("status") == "ERROR":
            continue
        lines = [
            f"# {row.get('title') or row['video_id']}",
            "",
            f"- Video ID: {row['video_id']}",
            f"- Source: {row.get('source_url','')}",
            f"- Candidate families detected: {', '.join(row.get('family_hits') or []) or 'UNCLASSIFIED'}",
            f"- Transcript method used for reconstruction: {row.get('transcript_method','')}",
            "",
            "## Rule evidence",
            "",
        ]
        for field, values in (row.get("fields") or {}).items():
            status = (row.get("field_status") or {}).get(field, "UNSPECIFIED")
            shown = "; ".join(values) if values else "UNSPECIFIED"
            lines.append(f"- **{field}** — {status}: {shown}")
        lines.extend([
            "",
            "## Reconstruction status",
            "",
            "- Source fidelity: SOURCE-EXPLICIT where deterministic evidence exists; otherwise UNSPECIFIED.",
            "- Phase status: RECONSTRUCTING.",
            "- No backtest or parameter tuning is performed in Phase 27 evidence extraction.",
        ])
        safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", row["video_id"]).strip("_") or "video"
        (rules_root / f"{safe}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    Path(args.out.parent / "phase27_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
