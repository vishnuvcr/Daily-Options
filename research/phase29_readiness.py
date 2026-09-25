#!/usr/bin/env python3
"""Phase 29.1 deterministic source-readiness audit.

This script does not download large market datasets and does not compute P&L.
It pins public source revisions, inventories their partition trees, maps those
capabilities to the 71 candidate rows, and keeps every candidate outside the
Phase 30 numerical gate until strategy-specific readiness is proven.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from huggingface_hub import HfApi, RepoFile
REVISIONS = {
    "trademarkk": {
        "repo": "thetrademarkk/india-index-options-1m",
        "revision": "51ca58c",
        "paths": ["index", "options/NIFTY", "options/BANKNIFTY", "options/SENSEX", "stocks_options"],
        "expected_schema": [
            "timestamp", "open", "high", "low", "close", "volume",
            "open_interest", "trading_day", "symbol", "strike", "option_type", "expiry"
        ],
        "oi_intraday": True,
    },
    "rissin": {
        "repo": "rissin/nse-options-intraday",
        "revision": "78b1c5468255d18cf492984bfe6fe4e3ac874d7c",
        "paths": [
            "upstox_intraday/NIFTY",
            "upstox_intraday/BANKNIFTY",
            "upstox_intraday/SENSEX",
            "historical_daily/NIFTY",
            "historical_daily/BANKNIFTY",
        ],
        "expected_schema": [
            "date", "timestamp", "underlying", "expiry", "strike", "option_type",
            "exercise_style", "open", "high", "low", "close", "volume", "oi",
            "settle_price", "source", "granularity"
        ],
        "oi_intraday": False,
    },
}

NSE_EVIDENCE = {
    "current_nifty_weekly_expiry": "TUESDAY (previous trading day if Tuesday is a trading holiday)",
    "nifty_lot_2024_04_26": 25,
    "nifty_lot_2024_11_20_new_contracts": 75,
    "nifty_lot_2026_01_06_first_weekly_revised_expiry": 65,
    "historical_rule": "Use contract-level dated circulars/contract master; never back-project current expiry or lot size across the full sample.",
}


def tree(repo: str, revision: str) -> list[RepoFile]:
    """Read the pinned Hub tree through the official Python client."""
    api = HfApi()
    items = list(
        api.list_repo_tree(
            repo_id=repo,
            path_in_repo=None,
            recursive=True,
            expand=False,
            revision=revision,
            repo_type="dataset",
            token=False,
        )
    )
    return [item for item in items if isinstance(item, RepoFile)]


def inventory_source(name: str, spec: dict) -> dict:
    result = {
        "repo": spec["repo"],
        "revision": spec["revision"],
        "paths": {},
        "expected_schema": spec["expected_schema"],
        "intraday_oi_available": spec["oi_intraday"],
        "api_status": "OK",
        "tree_file_count": 0,
    }
    try:
        rows = tree(spec["repo"], spec["revision"])
        all_paths = sorted(item.path for item in rows)
        result["tree_file_count"] = len(all_paths)
        for path in spec["paths"]:
            prefix = path.rstrip("/") + "/"
            files = [p for p in all_paths if p.startswith(prefix) and p.lower().endswith(".parquet")]
            result["paths"][path] = {
                "status": "PRESENT" if files else "EMPTY",
                "parquet_file_count": len(files),
                "sample_files": files[:3] + (files[-3:] if len(files) > 3 else []),
                "first_file": files[0] if files else None,
                "last_file": files[-1] if files else None,
            }
    except Exception as exc:
        result["api_status"] = "ERROR"
        for path in spec["paths"]:
            result["paths"][path] = {"status": "ERROR", "error": str(exc), "parquet_file_count": 0}
    return result



def classify(hint: str, inv: dict) -> tuple[str, str, str]:
    h = (hint or "").lower()
    if "covered_call" in h or "covered_or_equity" in h:
        stock = inv["trademarkk"]["paths"].get("stocks_options", {})
        if stock.get("status") == "PRESENT" and stock.get("parquet_file_count", 0) > 0:
            return ("DATA_LIMITED", "STOCK_OPTIONS_NEED_RULE_SPECIFIC_CONTRACT_COVERAGE",
                    "Stock-option tree exists at the pinned source, but strategy-specific symbol/expiry/strike completeness is not proven.")
        return ("DATA_LIMITED", "STOCK_OPTIONS_NOT_VERIFIED_AT_PIN",
                "The pinned Phase 29 index-option source has not verified stock-option contract coverage for this rule.")
    if "leaps" in h:
        return ("DATA_LIMITED", "LONG_DATED_CONTINUITY_NOT_VERIFIED",
                "Long-dated/LEAPS continuity and contract lifecycle coverage are not proven by the pinned 1-minute readiness sources.")
    if h == "unresolved" or not h.strip():
        return ("UNRESOLVED", "SOURCE_RULE_UNRESOLVED",
                "No stable canonical payoff-family requirement has yet been established.")
    if any(k in h for k in [
        "iron_condor", "iron_fly", "calendar", "diagonal", "ratio_spread",
        "strangle", "straddle", "debit_spread", "credit_spread", "jade_lizard", "gamma"
    ]):
        tm = inv["trademarkk"]["paths"].get("options/NIFTY", {})
        ri = inv["rissin"]["paths"].get("upstox_intraday/NIFTY", {})
        if tm.get("parquet_file_count", 0) > 0 and ri.get("parquet_file_count", 0) > 0:
            return ("PRELIMINARY_FEASIBLE", "INDEX_1M_PINNED_SOURCE_PRESENT",
                    "Pinned TradeMarkk and independent Rissin index-option partitions exist; strategy-specific expiry/strike/date quote completeness still requires validation.")
        return ("DATA_LIMITED", "INDEX_1M_PARTITION_MISSING",
                "At least one pinned independent index-option partition is unavailable.")
    return ("UNRESOLVED", "SOURCE_RULE_UNRESOLVED",
            "No stable canonical payoff-family requirement has yet been established.")


def load_families(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    family_path = Path("data/equity_income/strategy_families.csv")
    families = load_families(family_path)
    if len(families) != 71:
        raise AssertionError(f"Expected 71 candidate rows from Phase 28, found {len(families)}")

    inventory = {name: inventory_source(name, spec) for name, spec in REVISIONS.items()}
    inventory["nse_evidence"] = NSE_EVIDENCE
    inv_path = Path("data/equity_income/phase29_readiness_source_inventory.json")
    inv_path.parent.mkdir(parents=True, exist_ok=True)
    inv_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rows = []
    for fam in families:
        status, blocker, rationale = classify(fam.get("candidate_family_hint", ""), inventory)
        row = {
            "family_id": fam["family_id"],
            "video_id": fam["video_id"],
            "candidate_family_hint": fam.get("candidate_family_hint", ""),
            "cluster_confidence": fam.get("cluster_confidence", ""),
            "source_fidelity": fam.get("source_fidelity", ""),
            "trade_source_primary": REVISIONS["trademarkk"]["repo"],
            "trade_source_revision": REVISIONS["trademarkk"]["revision"],
            "independent_source": REVISIONS["rissin"]["repo"],
            "independent_source_revision": REVISIONS["rissin"]["revision"],
            "index_option_partition_present": "YES" if inventory["trademarkk"]["paths"].get("options/NIFTY", {}).get("parquet_file_count", 0) > 0 else "NO",
            "independent_nifty_partition_present": "YES" if inventory["rissin"]["paths"].get("upstox_intraday/NIFTY", {}).get("parquet_file_count", 0) > 0 else "NO",
            "ohlc_available": "YES",
            "bid_ask_available": "NO_VERIFIED_PUBLIC_SOURCE",
            "tradeMarkk_intraday_oi": "YES",
            "rissin_intraday_oi": "NO_DOCUMENTED_FOR_UPSTOX",
            "expiry_identity": "REQUIRES_CONTRACT_LEVEL_JOIN",
            "current_nifty_expiry": NSE_EVIDENCE["current_nifty_weekly_expiry"],
            "historical_lot_size_status": "PARTIALLY_OFFICIAL_MILESTONES_ONLY",
            "execution_price_model": "NEXT_AVAILABLE_1M_OPEN_PLUS_EXPLICIT_SLIPPAGE; NO_BID_ASK_INFERENCE",
            "india_vix": "AVAILABLE; JOIN LATER WITH INFORMATION BARRIER",
            "fii_dii": "AVAILABLE; JOIN LATER WITH INFORMATION BARRIER",
            "global_context": "DEFERRED_TO_PHASE31",
            "corporate_actions": "STRATEGY_DEPENDENT; NOT_A_CURRENT_BLOCKER_FOR_INDEX_OPTIONS",
            "feasibility_status": status,
            "readiness_blocker": blocker,
            "rationale": rationale,
            "backtest_allowed": "NO",
        }
        rows.append(row)

    out = Path("reports/phase29_readiness_matrix.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "candidate_members": len(rows),
        "preliminary_feasible": sum(r["feasibility_status"] == "PRELIMINARY_FEASIBLE" for r in rows),
        "data_limited": sum(r["feasibility_status"] == "DATA_LIMITED" for r in rows),
        "unresolved": sum(r["feasibility_status"] == "UNRESOLVED" for r in rows),
        "bid_ask_verified": 0,
        "strategy_specific_quote_completeness_verified": 0,
        "historical_lot_size_fully_verified": 0,
        "backtest_allowed": 0,
        "phase30_gate": "BLOCKED",
        "source_revision_pins": {
            "TradeMarkk": REVISIONS["trademarkk"]["revision"],
            "Rissin": REVISIONS["rissin"]["revision"],
        },
    }
    Path("reports/phase29_readiness_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
