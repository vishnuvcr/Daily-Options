#!/usr/bin/env python3
"""Phase 29 deterministic market-data feasibility report.

No prices are backtested here. This phase maps canonical candidate families
to verified source capabilities and explicit data limitations.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

SOURCES = {
    "index_1m": {
        "primary": "thetrademarkk/india-index-options-1m",
        "secondary": "rissin/nse-options-intraday",
        "coverage": "PRELIMINARY_1M_INDEX_OPTIONS",
        "oi": "TRADEMARKK_SCHEMA_OI; RISSIN_INTRADAY_OI_UNAVAILABLE",
    },
    "stock_options": {
        "primary": "NSE/historical + TradeMarkk repository stock-options area",
        "secondary": "Rissin index-options dataset",
        "coverage": "NOT_VERIFIED_FOR_STOCK_OPTION_RULES",
        "oi": "NOT_VERIFIED",
    },
    "long_dated": {
        "primary": "NSE contract/history + TradeMarkk where present",
        "secondary": "Rissin daily history where applicable",
        "coverage": "NOT_VERIFIED_FOR_LEAPS",
        "oi": "NOT_VERIFIED",
    },
}

def load_csv(path: Path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))

def classify(hint: str):
    h=(hint or "").lower()
    if "covered_call" in h or "covered_or_equity" in h:
        return "stock_options", "DATA_LIMITED", "The current verified 1-minute public sources are index-option focused; stock-option coverage must be proven before testing.", False
    if "leaps" in h:
        return "long_dated", "DATA_LIMITED", "Long-dated/LEAPS contract continuity is not yet verified from the cached 1-minute sources.", False
    if any(x in h for x in ["iron_condor","iron_fly","calendar","diagonal","ratio_spread","strangle","straddle","debit_spread","credit_spread","jade_lizard","gamma"]):
        return "index_1m", "PRELIMINARY_FEASIBLE", "Index-option 1-minute sources expose strike/expiry/OHLC; strategy-specific quote completeness and historical expiry/lot-size coverage still require validation.", True
    return "index_1m", "UNRESOLVED", "No stable canonical payoff-family requirement has yet been established.", False

def main() -> int:
    root=Path("data/equity_income")
    families=load_csv(root/"strategy_families.csv")
    rows=[]
    for row in families:
        source_key,status,rationale,has_1m=classify(row.get("candidate_family_hint",""))
        src=SOURCES[source_key]
        rows.append({
            "family_id":row["family_id"],
            "video_id":row["video_id"],
            "candidate_family_hint":row.get("candidate_family_hint","") ,
            "cluster_confidence":row.get("cluster_confidence","") ,
            "data_source_primary":src["primary"],
            "data_source_secondary":src["secondary"],
            "intraday_coverage":src["coverage"],
            "oi_availability":src["oi"],
            "expiry_identity":"REQUIRES_CONTRACT_LEVEL_JOIN",
            "historical_lot_size":"REQUIRES_HISTORICAL_CONTRACT_MASTER",
            "quote_completeness":"REQUIRES_STRATEGY_SPECIFIC_COVERAGE_TEST",
            "current_nifty_expiry":"NSE_TUESDAY",
            "fii_dii_source":"NSE_DAILY_REPORT_AVAILABLE",
            "india_vix_source":"NSE_HISTORICAL_VIX_AVAILABLE",
            "global_gold_context":"PHASE31_INPUT_NOT_YET_CACHED",
            "transaction_costs":"NSE_LEVIES_VERIFIED; PAYTM_TARIFF_LIVE_VERIFY_REQUIRED",
            "feasibility_status":status,
            "one_minute_path": "YES" if has_1m else "NO_OR_NOT_VERIFIED",
            "rationale":rationale,
            "backtest_allowed":"NO",
        })
    ]
    out=Path("reports/phase29_data_feasibility.csv")
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    summary={
        "candidate_members":len(rows),
        "preliminary_feasible":sum(r["feasibility_status"]=="PRELIMINARY_FEASIBLE" for r in rows),
        "data_limited":sum(r["feasibility_status"]=="DATA_LIMITED" for r in rows),
        "unresolved":sum(r["feasibility_status"]=="UNRESOLVED" for r in rows),
        "backtest_allowed":0,
        "quote_completeness_verified":0,
        "historical_lot_sizes_verified":0,
    }
    Path("reports/phase29_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())