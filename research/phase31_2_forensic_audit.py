#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, re
from datetime import date
from pathlib import Path
import duckdb
import pandas as pd

START=date(2021,7,1); END=date(2026,8,31)
ENTRY="09:30:00"; EXIT="15:10:00"
TOL=1e-6

def lot_size(expiry):
    d=pd.Timestamp(expiry).date()
    if d < date(2024,4,26): return 50
    if d < date(2024,11,21): return 25
    if d < date(2026,1,6): return 75
    return 65

def nearest_strike(px):
    return int(round(float(px)/50.0)*50)

def qpath(p): return str(p).replace("'","''")

def price(con, path, strike, side, ts):
    sql=f"""SELECT CAST(open AS DOUBLE) px
            FROM read_parquet('{qpath(path)}')
            WHERE CAST(timestamp AS TIMESTAMP)=TIMESTAMP '{ts}'
              AND CAST(strike AS DOUBLE)={float(strike)}
              AND UPPER(CAST(option_type AS VARCHAR))='{side}'
              AND CAST(open AS DOUBLE)>0 LIMIT 1"""
    x=con.execute(sql).df()
    return None if x.empty else float(x.iloc[0].px)

def index_price(con,path,ts):
    x=con.execute(f"""SELECT CAST(open AS DOUBLE) px FROM read_parquet('{qpath(path)}')
      WHERE CAST(timestamp AS TIMESTAMP)=TIMESTAMP '{ts}' LIMIT 1""").df()
    return None if x.empty else float(x.iloc[0].px)

def charge(price, action, qty, lot, d):
    gross=float(price)*qty*lot
    stt=gross*(0.001 if d<date(2026,4,1) else 0.0015) if action=="SELL" else 0.0
    exchange=gross*(0.0003503 if d<date(2026,3,1) else 0.000355299)
    sebi=gross*0.000001
    stamp=gross*0.00003 if action=="BUY" else 0.0
    brokerage=20.0
    gst=0.18*(brokerage+exchange+sebi)
    return brokerage+exchange+sebi+stt+stamp+gst

def parse_source_mismatch():
    p=Path("research/phase31_1_user_selected_nifty_ratio.py")
    txt=p.read_text(encoding="utf-8")
    return {
      "source_sha256": hashlib.sha256(txt.encode()).hexdigest(),
      "aggregates_nonexistent_costs_column": 'costs=("costs"' in txt,
      "aggregates_transaction_costs": 'costs=("transaction_costs"' in txt,
      "contains_exact_timestamp_lookup": "timestamp AS TIMESTAMP" in txt and "= TIMESTAMP" in txt,
      "contains_next_expiry_selection": "e >= day" in txt,
    }

def stratified_sample(trades, n=30):
    x=trades.copy()
    x["trade_date"]=pd.to_datetime(x["trade_date"]).dt.date
    picks=[]
    years=sorted(x.trade_date.map(lambda d:d.year).unique())
    for y in years:
        z=x[x.trade_date.map(lambda d:d.year)==y]
        if not z.empty: picks.append(z.iloc[len(z)//2])
    remaining=x.drop(index=[r.name for r in picks], errors="ignore")
    if len(picks)<n and not remaining.empty:
        idx=[int(round(i)) for i in pd.Series(range(n-len(picks))).map(lambda k:k*(len(remaining)-1)/max(n-len(picks)-1,1))]
        picks.extend([remaining.iloc[i] for i in idx])
    return pd.DataFrame(picks).drop_duplicates("trade_date").head(n)

def audit(data, out):
    out.mkdir(parents=True,exist_ok=True)
    base=Path("reports/phase31_1/base")
    trades=pd.read_csv(base/"trades.csv")
    weekly=pd.read_csv(base/"weekly.csv")
    summary=json.loads((base/"summary.json").read_text())
    index_path=data/"index"/"NIFTY.parquet"
    expiry_files={}
    for p in (data/"options"/"NIFTY").glob("*.parquet"):
        try:
            d=pd.Timestamp(p.stem).date()
        except Exception: continue
        if START<=d<=END: expiry_files[d]=p
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    sample=stratified_sample(trades,30)
    rows=[]; errors=[]
    for _,r in sample.iterrows():
        day=pd.Timestamp(r["trade_date"]).date()
        expiry=pd.Timestamp(r["expiry"]).date()
        ref_spot=float(r["spot_0930"])
        calc_spot=index_price(con,index_path,f"{day} {ENTRY}")
        exit_spot=index_price(con,index_path,f"{day} {EXIT}")
        future=[e for e in sorted(expiry_files) if e>=day]
        derived_expiry=future[0] if future else None
        atm=nearest_strike(calc_spot) if calc_spot is not None else None
        specs=[("CE",atm+200,"BUY",2),("PE",atm-200,"BUY",2),("PE",atm-400,"SELL",1)] if atm is not None else []
        raw_calc=exec_calc=tc_calc=0.0
        leg_ok=True
        leg_details=[]
        for side,strike,action,qty in specs:
            ep=price(con,expiry_files[expiry],strike,side,f"{day} {ENTRY}") if expiry in expiry_files else None
            xp=price(con,expiry_files[expiry],strike,side,f"{day} {EXIT}") if expiry in expiry_files else None
            key=(side,strike,action,qty)
            if ep is None or xp is None:
                leg_ok=False
                errors.append(f"{day}: missing raw leg {key}")
                continue
            slip=float(r["slippage_cost"])/max(sum(int(z["qty_lots"]) for z in ref_legs),1) if False else None
            # Infer the run's declared slippage from the phase report directory.
            s=float(r["total_costs"]-r["transaction_costs"])
            # total slippage is across all legs; reconstruct using quantity-weighted execution difference.
            # Compare raw values first; execution values are compared to the known Base slippage from run metadata.
            raw_pnl=(xp-ep)*qty*lot_size(expiry) if action=="BUY" else (ep-xp)*qty*lot_size(expiry)
            raw_calc+=raw_pnl
            slip_amt=0.20
            if action=="BUY":
                ee=ep+slip_amt; xx=max(0.0,xp-slip_amt); side_exit="SELL"
                ex_pnl=(xx-ee)*qty*lot_size(expiry)
            else:
                ee=max(0.0,ep-slip_amt); xx=xp+slip_amt; side_exit="BUY"
                ex_pnl=(ee-xx)*qty*lot_size(expiry)
            exec_calc+=ex_pnl
            tc=charge(ee,action,qty,lot_size(expiry),day)+charge(xx,side_exit,qty,lot_size(expiry),day)
            tc_calc+=tc
            leg_details.append({"key":list(key),"entry_raw":ep,"exit_raw":xp,"raw_pnl":raw_pnl,"tc":tc})
        if "gross_pnl_raw" in r.index:
            ref_raw_agg=float(r["gross_pnl_raw"])
            if abs(raw_calc-ref_raw_agg)>1e-5:
                leg_ok=False; errors.append(f"{day}: raw aggregate mismatch {raw_calc} vs {ref_raw_agg}")
        ref_exec_gross=float(r["gross_pnl"])
        if abs(exec_calc-ref_exec_gross)>1e-5:
            leg_ok=False; errors.append(f"{day}: execution gross mismatch {exec_calc} vs {ref_exec_gross}")
        ref_tc=float(r["transaction_costs"])
        if abs(tc_calc-ref_tc)>1e-5:
            leg_ok=False; errors.append(f"{day}: transaction-cost mismatch {tc_calc} vs {ref_tc}")
        ref_net=float(r["net_pnl"])
        calc_net=exec_calc-tc_calc
        if abs(calc_net-ref_net)>1e-5:
            leg_ok=False; errors.append(f"{day}: Base net mismatch {calc_net} vs {ref_net}")
        row={"trade_date":str(day),"expiry_ref":str(expiry),"expiry_derived":str(derived_expiry),"spot_ref":ref_spot,"spot_raw":calc_spot,"exit_spot_raw":exit_spot,
             "atm_ref":int(r["atm"]),"atm_derived":atm,"lot_ref":int(r["lot_size"]),"lot_derived":lot_size(expiry),
             "gross_ref":float(r["gross_pnl"]),"gross_recalc":exec_calc,"tc_ref":float(r["transaction_costs"]),"tc_recalc":tc_calc,
             "net_ref":ref_net,"net_recalc":calc_net,"match":leg_ok,"legs":json.dumps(leg_details,separators=(",",":"))}
        rows.append(row)
    con.close()
    rec=pd.DataFrame(rows)
    rec.to_csv(out/"sample_reconciliation.csv",index=False)

    # Independent aggregation checks using the persisted trade ledger.
    t=trades.copy()
    w=t.groupby(t["trade_date"].astype(str).str[:10].map(lambda s: pd.Timestamp(s).to_period("W-SUN").strftime("%Y-%m-%d/%Y-%m-%d")),as_index=False).agg(net_pnl=("net_pnl","sum"),gross_pnl=("gross_pnl","sum"),transaction_costs=("transaction_costs","sum"),trading_days=("trade_date","count"))
    w["positive"]=w.net_pnl>0
    total_net=float(t.net_pnl.sum())
    mean_week=float(w.net_pnl.mean())
    median_week=float(w.net_pnl.median())
    positive=float(w.positive.mean())
    weekly_cost_col="costs" if "costs" in weekly.columns else "total_costs"
    weekly_net_diff=float((w.net_pnl.sort_values("net_pnl").reset_index(drop=True)-weekly.net_pnl.sort_values("net_pnl").reset_index(drop=True)).abs().max())
    source=parse_source_mismatch()
    source["persisted_weekly_has_costs_column"]="costs" in weekly.columns
    source["reference_trade_has_cost_column"]="costs" in trades.columns
    diagnostics=[]
    for _,r in rec.iterrows():
        if pd.notna(r.exit_spot_raw):
            move=float(r.exit_spot_raw-r.spot_raw)
            diagnostics.append({"trade_date":r.trade_date,"spot_0930":r.spot_raw,"spot_1510":r.exit_spot_raw,"move_points":move,
              "central_band_low":r.atm_derived-200,"central_band_high":r.atm_derived+200,
              "inside_central_band":bool((r.exit_spot_raw>=r.atm_derived-200) and (r.exit_spot_raw<=r.atm_derived+200)),"net_pnl":r.net_ref})
    pd.DataFrame(diagnostics).to_csv(out/"payoff_diagnostics.csv",index=False)
    audit={
      "status":"COMPLETE","decision":"QUARANTINED" if errors or source["aggregates_nonexistent_costs_column"] else "VALIDATED",
      "sample_rows":len(rec),"sample_matches":int(rec.match.sum()) if not rec.empty else 0,
      "sample_mismatches":int((~rec.match).sum()) if not rec.empty else 0,
      "errors":errors,
      "source_report_schema_check":source,
      "reference_trade_days":int(len(t)),
      "reference_weeks":int(len(w)),
      "reference_total_net":total_net,
      "reference_summary_total_net":float(summary["total_net"]),
      "reference_total_net_diff":abs(total_net-float(summary["total_net"])),
      "reference_mean_week":mean_week,
      "reference_summary_mean_week":float(summary["mean_weekly_net"]),
      "reference_median_week":median_week,
      "reference_summary_median_week":float(summary["median_weekly_net"]),
      "reference_positive_week_rate":positive,
      "reference_summary_positive_week_rate":float(summary["positive_week_rate"]),
      "weekly_net_reconciliation_max_abs_diff":weekly_net_diff,
      "payoff_sample_inside_central_band_rate":float(pd.DataFrame(diagnostics)["inside_central_band"].mean()) if diagnostics else None,
      "note":"The central expiry band is a diagnostic; the 15:10 exit is not expiry and therefore this does not replace the actual mark-to-market P&L."
    }
    (out/"forensic_audit.json").write_text(json.dumps(audit,indent=2,default=str),encoding="utf-8")
    return audit

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(audit(args.data,args.out),indent=2,default=str))
