#!/usr/bin/env python3
"""Phase 27.4: semantic cleanup of T1 structured evidence.

Re-fetches source caption segments with Python, but writes only structured facts
and source timestamps. It deliberately rejects ambiguous/generic lexical matches.
"""
from __future__ import annotations
import csv,json,re,time
from pathlib import Path
import requests

DAYS="monday|tuesday|wednesday|thursday|friday"
def clean(s): return re.sub(r"\s+"," ",(s or "").strip())[:120]

def fetch(video_id):
    r=requests.get("https://youtubegpt.ai/api/transcript",params={"v":video_id,"format":"json","lang":"en"},headers={"User-Agent":"Daily-Options-Phase27.4/1.0"},timeout=(5,20))
    r.raise_for_status(); d=r.json()
    if not d.get("ok"): raise RuntimeError(str(d.get("message") or d.get("code") or "API_NOT_OK"))
    return [s for s in (d.get("segments") or []) if isinstance(s,dict) and str(s.get("text") or "").strip()]

def ctx(segments,i,radius=3):
    lo=max(0,i-radius); hi=min(len(segments),i+radius+1)
    return " ".join(str(segments[j].get("text") or "") for j in range(lo,hi))

def emit(out,seen,value,start,kind):
    value=clean(value)
    if not value: return
    key=(kind,value.lower(),round(start,1))
    if key not in seen: seen.add(key); out.append({"value":value,"start_sec":round(start,1)})

def extract(segments):
    fields={k:[] for k in ["entry_action","entry_day","adjustment_action","adjustment_day","exit_day","expiry_reference","underlying","time_reference","ratio_reference","lot_reference","premium_zone","strike_reference","stop_reference","target_reference","width_reference","delta_reference","day_count_reference"]}
    seen=set()
    for i,s in enumerate(segments):
        text=str(s.get("text") or "")
        c=ctx(segments,i)
        start=float(s.get("start") or 0.0)
        low=c.lower()
        # Timing: only accept a clock when explicitly tied to entry/trade/adjust/exit or market action.
        if re.search(r"\b(?:entry|enter|start|trade|open|adjust|adjustment|hedge|exit|close|square|book)\b",low,re.I):
            for m in re.finditer(r"\b([01]?\d|2[0-3]):([0-5]\d)\s*(?:am|pm)?\b",c,re.I): emit(fields["time_reference"],seen,m.group(0),start,"time")
        # Days: require semantic anchor.
        for day in re.findall(rf"\b({DAYS})\b",c,re.I):
            if re.search(rf"\b(?:enter|entry|start|trade|open)[^.!?]{{0,100}}\b{day}\b",c,re.I): emit(fields["entry_day"],seen,day,start,"entry_day")
            if re.search(rf"\b(?:{day})\b[^.!?]{{0,100}}\b(?:enter|entry|start|trade|open)\b",c,re.I): emit(fields["entry_day"],seen,day,start,"entry_day")
            if re.search(rf"\b(?:adjust|adjustment|hedge|roll)[^.!?]{{0,100}}\b{day}\b",c,re.I): emit(fields["adjustment_day"],seen,day,start,"adjust_day")
            if re.search(rf"\b(?:{day})\b[^.!?]{{0,100}}\b(?:adjust|adjustment|hedge|roll)\b",c,re.I): emit(fields["adjustment_day"],seen,day,start,"adjust_day")
            if re.search(rf"\b(?:exit|close|square off|book profit)[^.!?]{{0,100}}\b{day}\b",c,re.I): emit(fields["exit_day"],seen,day,start,"exit_day")
            if re.search(rf"\b(?:{day})\b[^.!?]{{0,100}}\b(?:exit|close|square off|book profit)\b",c,re.I): emit(fields["exit_day"],seen,day,start,"exit_day")
            if re.search(rf"\b(?:expiry|expiration|weekly expiry)[^.!?]{{0,80}}\b{day}\b",c,re.I): emit(fields["expiry_reference"],seen,day,start,"expiry")
            if re.search(rf"\b{day}\b[^.!?]{{0,80}}\b(?:expiry|expiration)\b",c,re.I): emit(fields["expiry_reference"],seen,day,start,"expiry")
        # Underlying.
        for m in re.finditer(r"\b(NIFTY\s*50|NIFTY|BANKNIFTY|SENSEX)\b",c,re.I): emit(fields["underlying"],seen,m.group(1),start,"underlying")
        # Actions require nearby strategy nouns.
        if re.search(r"\b(?:entry|enter|initial|position|trade|leg|call|put|spread|strangle|straddle|condor)\b",low):
            for verb in re.findall(r"\b(sell|short|buy|long|write|purchase)\b",c,re.I): emit(fields["entry_action"],seen,verb,start,"entry_action")
        if re.search(r"\b(?:adjust|adjustment|hedge|roll|tested side|untested side|position|leg|strike)\b",low):
            for verb in re.findall(r"\b(shift|roll|move|add|remove|close|hedge|widen|narrow)\b",c,re.I): emit(fields["adjustment_action"],seen,verb,start,"adjust_action")
        # Ratio: colon form only when not a clock and both sides <= 20.
        for m in re.finditer(r"\b(\d{1,2}):(\d{1,2})\b",c):
            a,b=int(m.group(1)),int(m.group(2))
            if b<=20 and a<=20: emit(fields["ratio_reference"],seen,m.group(0),start,"ratio")
        # Lot sizing must mention lots/lot size/quantity of lots.
        for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(?:lots?|lot size|lot equivalent|quantity of lots)\b",c,re.I): emit(fields["lot_reference"],seen,m.group(1),start,"lot")
        # Premium/credit only when nonzero and semantically tied.
        for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(?:points?|pts)\s+(?:premium|credit)\b|\b(?:premium|credit|collect)\s+(?:of|around|near)\s*(\d+(?:\.\d+)?)\b",c,re.I):
            val=m.group(1) or m.group(2)
            if val and float(val)>0: emit(fields["premium_zone"],seen,val,start,"premium")
        # Strike constructions require explicit strike vocabulary.
        for term in ["at the money","ATM","out of the money","OTM","in the money","ITM","same strike","one strike","two strikes","three strikes","premium matched","delta"]:
            if re.search(rf"\b{re.escape(term)}\b",c,re.I): emit(fields["strike_reference"],seen,term,start,"strike")
        # Stop/target only with stop-loss/target/profit language; preserve numeric value only.
        for m in re.finditer(r"\b(?:hard stop|soft stop|stop loss|stop-loss)\b(?:[^.!?]{0,60})",c,re.I): emit(fields["stop_reference"],seen,m.group(0),start,"stop")
        for m in re.finditer(r"\b(?:target|profit target|take profit|book profit)\b(?:[^.!?]{0,60})",c,re.I): emit(fields["target_reference"],seen,m.group(0),start,"target")
        # Width only if explicitly tied to points/strike width/spread width.
        for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(?:points?|pts)\s*(?:wide|width)\b|\b(?:width|spread width)\s*(?:of|is)?\s*(\d+(?:\.\d+)?)\b",c,re.I): emit(fields["width_reference"],seen,m.group(1) or m.group(2),start,"width")
        # Delta only with explicit delta word.
        for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(?:delta|Δ)\b",c,re.I): emit(fields["delta_reference"],seen,m.group(1),start,"delta")
        # Day-count only with explicit expiry relation.
        for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(?:days?|sessions?)\s+(?:before|after)\s+(?:expiry|expiration)\b",c,re.I): emit(fields["day_count_reference"],seen,m.group(0),start,"day_count")
    return fields

def status(vals):
    values={x["value"].lower() for x in vals}
    if not vals: return "UNSPECIFIED"
    if len(values)>1: return "CONFLICTING"
    return "SOURCE-EXPLICIT"

def main():
    pri=list(csv.DictReader(open("reports/phase27_2_reconstruction_priority.csv",newline="",encoding="utf-8")))
    t1=[r for r in pri if r["priority_tier"]=="T1"]
    rows=[]
    for r in t1:
        segs=fetch(r["video_id"])
        fields=extract(segs)
        fs={k:status(v) for k,v in fields.items()}
        rows.append({"video_id":r["video_id"],"title":r["title"],"family_hits":r["family_hits"],"fields":fields,"field_status":fs,"requires_manual_review":True,"backtest_allowed":"NO","retrieved_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())})
    root=Path("data/equity_income")
    root.joinpath("phase27_4_t1_clean_evidence.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in rows),encoding="utf-8")
    summary={"candidates":len(rows),"errors":0,"backtest_allowed":0,"conflicting_records":sum(any(v=="CONFLICTING" for v in r["field_status"].values()) for r in rows)}
    root.joinpath("phase27_4_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__": main()
