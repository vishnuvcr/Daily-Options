#!/usr/bin/env python3
"""Phase 29.2 deterministic contract-coverage audit.

Metadata-only: no P&L, no parameter optimisation, and no transcript
decryption. Uses frozen Phase 28 titles/family hints, archive manifests,
and the Phase 29.1 pinned source inventory.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

PRIMARY = "thetrademarkk/india-index-options-1m"
PRIMARY_REV = "51ca58c"
INDEPENDENT = "rissin/nse-options-intraday"
INDEPENDENT_REV = "78b1c5468255d18cf492984bfe6fe4e3ac874d7c"


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def infer_underlying(title: str, hint: str) -> str:
    text = f"{title} {hint}".upper()
    if "NIFTY / BANKNIFTY" in text or "NIFTY/BANKNIFTY" in text:
        return "MULTI_INDEX"
    if "BANKNIFTY" in text:
        return "BANKNIFTY"
    if "SENSEX" in text:
        return "SENSEX"
    if "NIFTY" in text:
        return "NIFTY"
    if "STOCK OPTIONS" in text or "STOCK OPTION" in text or "COVERED CALL" in text or "FROG JUMP" in text:
        return "STOCK"
    return "UNKNOWN"


def expiry_requirement(title: str, hint: str) -> str:
    text = f"{title} {hint}".lower()
    if "leaps" in text:
        return "LEAPS_OR_LONG_DATED"
    if any(k in text for k in ["calendar", "diagonal", "ratio_spread", "cross calendar", "double calendar"]):
        return "MULTI_EXPIRY"
    if any(k in text for k in ["weekly", "expiry day", "intraday"]):
        return "WEEKLY_OR_INTRADAY"
    return "EXPIRY_UNRESOLVED"


def path_counts(inv: dict, underlying: str) -> tuple[int, int, str]:
    tm = inv["trademarkk"]["paths"]
    ri = inv["rissin"]["paths"]
    if underlying == "NIFTY":
        return tm.get("options/NIFTY", {}).get("parquet_file_count", 0), ri.get("upstox_intraday/NIFTY", {}).get("parquet_file_count", 0), "options/NIFTY"
    if underlying == "BANKNIFTY":
        return tm.get("options/BANKNIFTY", {}).get("parquet_file_count", 0), ri.get("upstox_intraday/BANKNIFTY", {}).get("parquet_file_count", 0), "options/BANKNIFTY"
    if underlying == "SENSEX":
        return tm.get("options/SENSEX", {}).get("parquet_file_count", 0), ri.get("upstox_intraday/SENSEX", {}).get("parquet_file_count", 0), "options/SENSEX"
    if underlying == "STOCK":
        return tm.get("stocks_options", {}).get("parquet_file_count", 0), 0, "stocks_options"
    if underlying == "MULTI_INDEX":
        total_primary = sum(tm.get(k, {}).get("parquet_file_count", 0) for k in ("options/NIFTY", "options/BANKNIFTY", "options/SENSEX"))
        total_ind = sum(ri.get(k, {}).get("parquet_file_count", 0) for k in ("upstox_intraday/NIFTY", "upstox_intraday/BANKNIFTY", "upstox_intraday/SENSEX"))
        return total_primary, total_ind, "options/{NIFTY,BANKNIFTY,SENSEX}"
    return 0, 0, ""


def classify(row: dict, inv: dict, archived_ids: set[str]) -> dict:
    title = row["title"]
    hint = row.get("candidate_family_hint", "")
    underlying = infer_underlying(title, hint)
    expiry = expiry_requirement(title, hint)
    primary_count, independent_count, source_path = path_counts(inv, underlying)
    archived = row["video_id"] in archived_ids

    if not archived:
        state = "PROVENANCE_MISSING"
    elif "unresolved" in (hint or "").lower():
        state = "RULE_RECONSTRUCTION_REQUIRED"
    elif underlying == "UNKNOWN":
        state = "UNDERLYING_UNRESOLVED"
    elif expiry == "LEAPS_OR_LONG_DATED":
        state = "LONG_DATED_DATA_LIMITED"
    elif primary_count <= 0:
        state = "PRIMARY_DATA_MISSING"
    elif underlying in {"STOCK"}:
        state = "DATA_PARTIAL_INDEPENDENT_GAP"
    elif independent_count <= 0:
        state = "DATA_PARTIAL_INDEPENDENT_GAP"
    else:
        state = "CONTRACT_READY_FOR_CONTENT_JOIN"

    return {
        "family_id": row["family_id"],
        "video_id": row["video_id"],
        "title": title,
        "candidate_family_hint": hint,
        "cluster_confidence": row.get("cluster_confidence", ""),
        "source_fidelity": row.get("source_fidelity", ""),
        "underlying_inferred": underlying,
        "expiry_requirement": expiry,
        "primary_source": PRIMARY,
        "primary_revision": PRIMARY_REV,
        "primary_partition_path": source_path,
        "primary_parquet_file_count": primary_count,
        "independent_source": INDEPENDENT if independent_count > 0 else "",
        "independent_revision": INDEPENDENT_REV if independent_count > 0 else "",
        "independent_parquet_file_count": independent_count,
        "archive_provenance_present": "YES" if archived else "NO",
        "historical_lot_size": "REQUIRES_DATED_NSE_CONTRACT_JOIN",
        "historical_expiry_rule": "REQUIRES_DATED_NSE_RULE_JOIN",
        "quote_quality": "OHLCV_PUBLIC; BID_ASK_NOT_VERIFIED",
        "readiness_state": state,
        "backtest_allowed": "NO",
    }


def main() -> int:
    families = load_csv(Path("data/equity_income/strategy_families.csv"))
    if len(families) != 71:
        raise AssertionError(f"Expected 71 Phase 28 rows, found {len(families)}")

    inventory = json.loads(Path("data/equity_income/phase29_readiness_source_inventory.json").read_text(encoding="utf-8"))
    videos = load_jsonl(Path("data/equity_income/video_manifest.jsonl"))
    transcripts = load_jsonl(Path("data/equity_income/transcript_manifest.jsonl"))

    video_ids = {r.get("video_id") for r in videos if r.get("video_id")}
    transcript_ids = {r.get("video_id") for r in transcripts if r.get("video_id") and r.get("status") == "archived"}
    archived_ids = video_ids & transcript_ids

    rows = [classify(r, inventory, archived_ids) for r in families]

    out = Path("reports/phase29_2_contract_coverage_matrix.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    states: dict[str, int] = {}
    underlying_counts: dict[str, int] = {}
    for r in rows:
        states[r["readiness_state"]] = states.get(r["readiness_state"], 0) + 1
        underlying_counts[r["underlying_inferred"]] = underlying_counts.get(r["underlying_inferred"], 0) + 1

    summary = {
        "candidate_rows": len(rows),
        "archive_discovered_videos": len(videos),
        "archive_transcripts_status_archived": sum(r.get("status") == "archived" for r in transcripts),
        "candidate_archive_provenance": sum(r["archive_provenance_present"] == "YES" for r in rows),
        "all_rows_backtest_no": all(r["backtest_allowed"] == "NO" for r in rows),
        "matrix_row_count": len(rows),
        "readiness_state_counts": states,
        "underlying_counts": underlying_counts,
        "primary_trade_source_revision": PRIMARY_REV,
        "independent_source_revision": INDEPENDENT_REV,
        "backtest_allowed": 0,
        "phase30_gate": "BLOCKED",
        "notes": [
            "CONTRACT_READY_FOR_CONTENT_JOIN is not P&L readiness.",
            "No transcript plaintext was decrypted by this phase.",
            "Historical lot size and expiry remain date-specific official-exchange joins.",
            "Bid/ask remains unverified; later simulations must use an explicit OHLC execution/slippage model.",
        ],
    }
    Path("reports/phase29_2_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "phase": "29.2",
        "archive_discovered_videos": len(videos),
        "archive_transcript_records": len(transcripts),
        "archive_transcripts_status_archived": sum(r.get("status") == "archived" for r in transcripts),
        "primary": {"repo": PRIMARY, "revision": PRIMARY_REV},
        "independent": {"repo": INDEPENDENT, "revision": INDEPENDENT_REV},
        "contract_content_status": "NOT_YET_VALIDATED",
    }
    Path("data/equity_income/phase29_2_contract_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
