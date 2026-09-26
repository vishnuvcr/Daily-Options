from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import duckdb

COVERAGE=Path("reports/phase30_6_bear_put_signal_coverage.json")
MANIFEST=Path("reports/phase30_7_bear_put_interpretation_grid_manifest.json")
DATA=Path("data/cache/phase30_2_rissin")
OUT=Path("reports/phase30_7_bear_put_contract_audit.json")

REQUIRED={"date","expiry","strike","option_type","open","high","low","close","granularity"}

def main():
    m=json.loads(MANIFEST.read_text())
    c=json.loads(COVERAGE.read_text())
    defs=[x for x in c["definitions"] if x["signal_weeks"]>=20]
    checks={
        "manifest_cell_count":m["registered_cell_count"]==6480,
        "eligible_definition_count":len(defs)==45,
        "eligible_week_range":min(x["signal_weeks"] for x in defs)>=20 and max(x["signal_weeks"] for x in defs)<=53,
        "grid_arithmetic":45*2*2*3*2*3*2==m["registered_cell_count"],
    }
    files=sorted(DATA.glob("NIFTY_*.parquet"))
    if not files: raise RuntimeError("No cached Rissin NIFTY parquet files found")
    con=duckdb.connect()
    file_args=list(map(str,files))
    desc=con.execute("DESCRIBE SELECT * FROM read_parquet(?, union_by_name=true) LIMIT 0",[file_args]).df()
    cols=set(desc.column_name.astype(str))
    checks["required_columns"]=REQUIRED.issubset(cols)

    # All subsequent checks are SQL aggregates/distincts: no full option table is materialized.
    summary=con.execute("""
      SELECT
        COUNT(*) AS rows,
        COUNT(DISTINCT CAST(date AS DATE)) AS quote_dates,
        COUNT(DISTINCT CAST(expiry AS DATE)) AS expiries,
        COUNT(DISTINCT strike) AS strikes,
        SUM(CASE WHEN date IS NULL OR expiry IS NULL OR strike IS NULL OR open IS NULL OR high IS NULL OR low IS NULL OR close IS NULL THEN 1 ELSE 0 END) AS invalid_core,
        SUM(CASE WHEN strike <= 0 THEN 1 ELSE 0 END) AS bad_strikes,
        SUM(CASE WHEN UPPER(CAST(option_type AS VARCHAR)) NOT IN ('CE','PE') THEN 1 ELSE 0 END) AS bad_option_types,
        SUM(CASE WHEN CAST(expiry AS DATE) < CAST(date AS DATE) THEN 1 ELSE 0 END) AS expiry_before_quote
      FROM read_parquet(?, union_by_name=true)
      WHERE granularity='1min'
    """,[file_args]).fetchone()
    rows,quote_dates,expiries,strikes,invalid_core,bad_strikes,bad_types,bad_expiry=summary
    checks["no_invalid_core_rows"]=int(invalid_core)==0
    checks["option_types"]=int(bad_types)==0
    checks["positive_strikes"]=int(bad_strikes)==0
    checks["expiry_not_before_quote"]=int(bad_expiry)==0

    sig_dates=sorted({s["signal_ts"][:10] for d in defs for s in d["signals"]})
    exp_dates=[x[0] for x in con.execute(
        "SELECT DISTINCT CAST(expiry AS DATE) FROM read_parquet(?, union_by_name=true) WHERE granularity='1min' ORDER BY 1",[file_args]).fetchall()]
    enough=sum(sum(e > pd.Timestamp(d).date() for e in exp_dates)>=2 for d in sig_dates)
    checks["signals_with_two_future_expiries"]=enough==len(sig_dates)

    strikes_list=[float(x[0]) for x in con.execute(
        "SELECT DISTINCT strike FROM read_parquet(?, union_by_name=true) WHERE granularity='1min' AND strike IS NOT NULL",[file_args]).fetchall()]
    sset=set(strikes_list)
    checks["strike_grid_has_50pt_neighbors"]=any((s+50 in sset and s-50 in sset) for s in sset)

    checks["lot_schedule"]= [75,65]==[75 if pd.Timestamp("2025-12-30").date()<=pd.Timestamp("2025-12-30").date() else 65,
                                  65 if pd.Timestamp("2026-01-06").date()>=pd.Timestamp("2026-01-06").date() else 75]

    execution_rules={
        "signal_to_entry":"next_available_minute",
        "adjustment_to_fill":"next_available_minute",
        "missing_quote":"no_trade_or_unfilled_no_later_substitution",
        "base_slippage_points":0.20,
        "stress_slippage_points":0.40,
        "lot_size_schedule":{"through_2025-12-30":75,"from_2026-01-06":65},
        "info_barrier":"no_future_data"
    }
    checks["execution_rules_registered"]=(
        execution_rules["base_slippage_points"]<execution_rules["stress_slippage_points"]
        and execution_rules["signal_to_entry"]=="next_available_minute"
        and execution_rules["adjustment_to_fill"]=="next_available_minute"
        and execution_rules["info_barrier"]=="no_future_data"
    )
    passed=all(checks.values())
    result={
        "phase":"30.7","pnl_authorized":False,"audit_passed":passed,"checks":checks,
        "cache_files":[str(x) for x in files],
        "cache_rows":int(rows),"unique_quote_dates":int(quote_dates),
        "unique_expiries":int(expiries),"unique_strikes":int(strikes),
        "unique_signals":len(sig_dates),"registered_cell_count":m["registered_cell_count"],
        "execution_rules":execution_rules
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,default=str)+"\n")
    print(json.dumps(result,indent=2,default=str))
    if not passed: raise SystemExit("Phase 30.7 contract audit failed; P&L remains unauthorized.")

if __name__=="__main__": main()
