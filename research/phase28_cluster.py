#!/usr/bin/env python3
"""Phase 28 deterministic candidate clustering.

Uses Phase 26 titles plus Phase 27 family metadata. No backtests or promotions.
"""
from __future__ import annotations
import csv
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

STRUCTURAL = {
    "iron_condor", "iron_fly", "calendar", "diagonal", "ratio_spread",
    "strangle", "straddle", "covered_call", "jade_lizard",
    "credit_spread", "debit_spread", "leaps",
}

def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()

def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))

def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]

def structural_families(row: dict) -> set[str]:
    values = set(x for x in row.get("candidate_payoff_family", "").split("|") if x in STRUCTURAL)
    values.update(x for x in row.get("family_hits", []) if x in STRUCTURAL)
    return values

def similarity(a: dict, b: dict) -> float:
    ta, tb = norm(a.get("title", "")), norm(b.get("title", ""))
    title_ratio = SequenceMatcher(None, ta, tb).ratio()
    fa, fb = structural_families(a), structural_families(b)
    union = len(fa | fb)
    jacc = len(fa & fb) / union if union else 0.0
    return 0.65 * title_ratio + 0.35 * jacc

def cluster(rows: list[dict]) -> list[dict]:
    groups: list[list[dict]] = []
    for row in sorted(rows, key=lambda r: (norm(r.get("title", "")), r.get("video_id", ""))):
        best_idx, best_score = None, 0.0
        for idx, group in enumerate(groups):
            score = max(similarity(row, member) for member in group)
            if score > best_score:
                best_idx, best_score = idx, score
        if best_idx is not None and best_score >= 0.74:
            groups[best_idx].append(row)
        else:
            groups.append([row])
    output = []
    for idx, group in enumerate(groups, 1):
        hints = sorted({
            fam for row in group for fam in structural_families(row)
        }) or ["unresolved"]
        high = len(group) > 1 and len(hints) == 1 and hints[0] != "unresolved"
        for row in group:
            output.append({
                "family_id": f"EIG{idx:03d}",
                "video_id": row["video_id"],
                "title": row.get("title", ""),
                "source_url": row.get("webpage_url", ""),
                "candidate_family_hint": "|".join(hints),
                "cluster_size": len(group),
                "cluster_confidence": "HIGH" if high else "REVIEW_REQUIRED",
                "source_fidelity": "UNRESOLVED",
                "rule_status": "UNRESOLVED",
                "backtest_allowed": "NO",
            })
    return output

def main() -> int:
    root = Path("data/equity_income")
    inventory = load_csv(root / "video_inventory.csv")
    evidence = {r["video_id"]: r for r in load_jsonl(root / "phase27_rule_evidence.jsonl")}
    candidates = []
    for row in inventory:
        if row.get("candidate_payoff_family") == "unclassified":
            continue
        enriched = dict(row)
        enriched["family_hits"] = evidence.get(row["video_id"], {}).get("family_hits", [])
        candidates.append(enriched)
    result = cluster(candidates)
    out = root / "strategy_families.csv"
    fields = list(result[0].keys()) if result else []
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result)
    summary = {
        "candidate_videos": len(candidates),
        "family_clusters": len({r["family_id"] for r in result}),
        "high_confidence_members": sum(r["cluster_confidence"] == "HIGH" for r in result),
        "review_required_members": sum(r["cluster_confidence"] == "REVIEW_REQUIRED" for r in result),
        "backtest_allowed_members": sum(r["backtest_allowed"] == "YES" for r in result),
    }
    (root / "phase28_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
