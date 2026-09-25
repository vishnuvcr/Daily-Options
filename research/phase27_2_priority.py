#!/usr/bin/env python3
"""Phase 27.2 evidence-completeness prioritization.

Ranks candidates for manual source reconciliation by evidence completeness only.
It is not a performance ranking and it never authorizes backtesting.
"""
from __future__ import annotations
import csv,json
from pathlib import Path

MATERIAL=["entry_action","entry_day","adjustment_action","adjustment_day","exit_day","strike_reference","stop_reference","target_reference","underlying","lot_reference","time_reference","expiry_reference","premium_zone","ratio_reference","width_reference","delta_reference","day_count_reference"]

def load_jsonl(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def main():
    root=Path("data/equity_income")
    rows=load_jsonl(root/"phase27_1_rule_evidence.jsonl")
    out=[]
    for r in rows:
        fs=r.get("field_status",{})
        explicit=sum(fs.get(f)=="SOURCE-EXPLICIT" for f in MATERIAL)
        conflicting=sum(fs.get(f)=="CONFLICTING" for f in MATERIAL)
        missing=sum(fs.get(f) in {None,"UNSPECIFIED"} for f in MATERIAL)
        score=2*explicit-conflicting
        if score>=10: tier="T1"
        elif score>=6: tier="T2"
        else: tier="T3"
        out.append({
          "priority_score":score,
          "priority_tier":tier,
          "video_id":r["video_id"],
          "title":r.get("title",""),
          "family_hits":"|".join(r.get("family_hits",[])),
          "explicit_material_fields":explicit,
          "conflicting_material_fields":conflicting,
          "missing_material_fields":missing,
          "requires_manual_review":"YES",
          "backtest_allowed":"NO",
          "web_evidence":"FOUND" if r["video_id"] in {"aRjY_O6U3nQ","3dKrtjyX4hc","1V-06qTH5Rc","s1j4F8CYaTM"} else "NOT_YET_CURATED"
        })
    out.sort(key=lambda x:(x["priority_score"],x["explicit_material_fields"],-x["conflicting_material_fields"]),reverse=True)
    path=Path("reports/phase27_2_reconstruction_priority.csv"); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as fh:
      w=csv.DictWriter(fh,fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    summary={"candidates":len(out),"t1":sum(x["priority_tier"]=="T1" for x in out),"t2":sum(x["priority_tier"]=="T2" for x in out),"t3":sum(x["priority_tier"]=="T3" for x in out),"backtest_allowed":0}
    Path("reports/phase27_2_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__": main()