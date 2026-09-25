#!/usr/bin/env python3
"""Phase 27.3: generate source-fidelity rule sheets for T1 candidates.

The output contains only structured evidence values/timestamps and curated
external-description corroboration. It never stores transcript sentences and
never marks a candidate backtest-eligible.
"""
from __future__ import annotations
import csv,json,re
from pathlib import Path

def load_jsonl(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def load_csv(path):
    with path.open(encoding="utf-8",newline="") as fh: return list(csv.DictReader(fh))

def safe_name(video_id,title):
    base=re.sub(r"[^A-Za-z0-9]+","-",title).strip("-").lower()[:70]
    return f"{video_id}__{base}.md"

def render(record, external):
    title=record.get("title","")
    lines=[
      f"# {title}",
      "",
      f"- Video ID: `{record['video_id']}`",
      f"- Source URL: {record.get('source_url','')}",
      f"- Candidate families: {', '.join(record.get('family_hits',[])) or 'UNRESOLVED'}",
      "- Research status: SOURCE-FIDELITY REVIEW",
      "- Backtest allowed: NO",
      "",
      "## Structured source evidence"
    ]
    for field, values in record.get("fields",{}).items():
        status=record.get("field_status",{}).get(field,"UNSPECIFIED")
        lines.append(f"### {field} — {status}")
        if not values: lines.append("- UNSPECIFIED")
        else:
            for v in values[:8]: lines.append(f"- {v.get('value','')} — source timestamp {v.get('start_sec',0):.1f}s")
        lines.append("")
    lines += ["## External corroboration"]
    if external:
        lines += [f"- Source: {external.get('source_url','')}", f"- Source type: {external.get('source_type','')}"]
        for item in external.get("evidence",[]): lines.append(f"- {item}")
        lines += [f"- Research use: {external.get('research_use','')}"]
    else:
        lines.append("- No curated external corroboration yet; archived source captions remain primary.")
    lines += ["", "## Rule status", "- Entry rule: UNRESOLVED until exact trigger is reconciled.", "- Strike rule: UNRESOLVED until exact construction is reconciled.", "- Adjustment rule: UNRESOLVED until trigger/action pair is reconciled.", "- Stop rule: UNRESOLVED until numeric or event condition is reconciled.", "- Target/exit rule: UNRESOLVED until numeric/time condition is reconciled.", "- Capital/lots: UNRESOLVED until historically reproducible.", "- Paytm Money/NSE costs: NOT APPLIED IN PHASE 27.3.", "- Backtest promotion: BLOCKED."]
    return "\n".join(lines)+"\n"

def main():
    root=Path("data/equity_income")
    pri=load_csv(Path("reports/phase27_2_reconstruction_priority.csv"))
    evidence={r["video_id"]:r for r in load_jsonl(root/"phase27_1_rule_evidence.jsonl")}
    external=json.loads((root/"phase27_2_external_evidence.json").read_text(encoding="utf-8"))
    t1=[r for r in pri if r["priority_tier"]=="T1"]
    outdir=Path("docs/equity_income_strategy_rules/t1")
    outdir.mkdir(parents=True,exist_ok=True)
    rows=[]
    for p in t1:
        r=evidence[p["video_id"]]
        ext=external.get(p["video_id"])
        path=outdir/safe_name(p["video_id"],p["title"])
        path.write_text(render(r,ext),encoding="utf-8")
        rows.append({"video_id":p["video_id"],"title":p["title"],"priority_score":p["priority_score"],"family_hits":p["family_hits"],"rule_sheet":str(path),"backtest_allowed":"NO"})
    Path("reports/phase27_3_t1_manifest.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"t1_candidates":len(t1),"rule_sheets":len(rows),"backtest_allowed":0},sort_keys=True))

if __name__=="__main__": main()
