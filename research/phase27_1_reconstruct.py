#!/usr/bin/env python3
"""Phase 27.1 context-aware source-fidelity extraction.

Uses timestamped caption segments and small local windows to extract structured
facts without storing transcript sentences. This remains evidence gathering, not
backtesting and not LLM transcription.
"""
from __future__ import annotations
import csv, json, re, time
from pathlib import Path
import requests

DAY = r"monday|tuesday|wednesday|thursday|friday|saturday|sunday"
NUM = r"(?:\d+(?:\.\d+)?)"
TIME = rf"(?:[01]?\d|2[0-3]):[0-5]\d(?:\s?(?:am|pm))?"

PATTERNS = {
  "entry_day": [rf"(?:enter|entry|start|initiat\w*|take the trade|place the trade)[^.!?]{{0,160}}({DAY})", rf"({DAY})[^.!?]{{0,120}}(?:entry|enter|start)"],
  "adjustment_day": [rf"(?:adjust|adjustment|hedge|roll)[^.!?]{{0,160}}({DAY})", rf"({DAY})[^.!?]{{0,120}}(?:adjust|hedge|roll)"],
  "exit_day": [rf"(?:exit|close|square off|book profit)[^.!?]{{0,160}}({DAY})", rf"({DAY})[^.!?]{{0,120}}(?:exit|close|square)"],
  "underlying": [r"\b(NIFTY\s*50|NIFTY|BANKNIFTY|SENSEX)\b"],
  "time_reference": [rf"\b({TIME})\b"],
  "expiry_reference": [rf"\b({DAY})\s+(?:expiry|expiration)\b", rf"\b(?:expiry|expiration)[^.!?]{{0,80}}({DAY})\b", r"\bweekly expiry\b"],
  "lot_reference": [rf"\b({NUM})\s*(?:lots?|lot|lot equivalents?)\b", r"\b(\d+:\d+(?::\d+)?)\b"],
  "premium_zone": [rf"\b({NUM})\s*(?:point|points|pts)\s+(?:premium|credit|zone)\b", rf"\b(?:premium|credit|collect|zone)[^.!?]{{0,90}}({NUM})\s*(?:point|points|pts)?\b"],
  "strike_reference": [r"\b(at the money|ATM|out of the money|OTM|in the money|ITM|same strike|one strike|two strikes|three strikes|premium matched|delta)\b"],
  "stop_reference": [rf"\b(?:stop loss|hard stop|soft stop|stop)[^.!?]{{0,120}}((?:₹|rs\.?|rupees?)?\s*{NUM}(?:\s?%)?(?:\s?(?:points?|x|times))?)?\b", rf"\b({NUM}\s?%)\s+(?:stop|stop-loss)\b"],
  "target_reference": [rf"\b(?:target|profit target|book profit|take profit)[^.!?]{{0,120}}((?:₹|rs\.?|rupees?)?\s*{NUM}(?:\s?%)?(?:\s?(?:points?|x|times))?)?\b", rf"\b({NUM}\s?%)\s+(?:target|profit)\b"],
  "entry_action": [r"\b(sell|short|buy|long|write|purchase|sell the call|sell the put|buy the call|buy the put)\b"],
  "adjustment_action": [r"\b(shift|roll|move|add|remove|close|hedge|buy hedge|sell hedge|widen|narrow)\b"],
  "ratio_reference": [r"\b(\d+:\d+(?::\d+)?)\b", r"\b(?:one|two|three|four|five)\s*(?:to|:|-|for)\s*(?:one|two|three|four|five)\b"],
  "width_reference": [rf"\b({NUM})\s*(?:points?|strikes?)\s*(?:wide|width)?\b"],
  "delta_reference": [rf"\b({NUM})\s*(?:delta|Δ)\b", r"\b(\d+)\s*[-–]\s*(\d+)\s*delta\b"],
  "day_count_reference": [rf"\b({NUM})\s*(?:days?|sessions?)\s+(?:before|after|to)\s+(?:expiry|expiration)\b"],
}

def fetch(video_id: str):
    r=requests.get("https://youtubegpt.ai/api/transcript",params={"v":video_id,"format":"json","lang":"en"},headers={"User-Agent":"Daily-Options-Phase27.1/1.0"},timeout=(5,20))
    r.raise_for_status(); data=r.json()
    if not data.get("ok"): raise RuntimeError(str(data.get("message") or data.get("code") or "API_NOT_OK"))
    return [s for s in (data.get("segments") or []) if isinstance(s,dict) and str(s.get("text") or "").strip()]

def clean_value(v: str):
    return re.sub(r"\s+"," ",(v or "").strip())[:100]

def extract(field: str, windows):
    seen=set(); out=[]
    for start_sec, text in windows:
        for pat in PATTERNS[field]:
            for m in re.finditer(pat,text,flags=re.I):
                value=clean_value(m.group(1) if m.lastindex else m.group(0))
                if not value: continue
                key=(value.lower(),round(start_sec,1))
                if key in seen: continue
                seen.add(key); out.append({"value":value,"start_sec":round(start_sec,1)})
                if len(out)>=15: return out
    return out

def windows(segments):
    result=[]
    for i, seg in enumerate(segments):
        lo=max(0,i-3); hi=min(len(segments),i+4)
        text=" ".join(str(segments[j].get("text") or "") for j in range(lo,hi))
        result.append((float(segments[i].get("start") or 0.0),text))
    return result

def status(values):
    vals={v["value"].lower() for v in values}
    if not values: return "UNSPECIFIED"
    if len(vals)>1: return "CONFLICTING"
    return "SOURCE-EXPLICIT"

def family_hits(text):
    low=text.lower()
    terms={
      "iron_fly":["iron fly","ironfly"],"iron_condor":["iron condor","condor"],
      "calendar":["calendar"],"diagonal":["diagonal"],"ratio_spread":["ratio spread","ratio"],
      "strangle":["strangle"],"straddle":["straddle"],"covered_call":["covered call"],
      "credit_spread":["credit spread"],"debit_spread":["debit spread"],
      "leaps":["leaps"],"jade_lizard":["jade lizard"],
    }
    return [k for k,v in terms.items() if any(t in low for t in v)]

def build(video_id,title,url,segments):
    wins=windows(segments); full=" ".join(str(s.get("text") or "") for s in segments)
    fields={f:extract(f,wins) for f in PATTERNS}
    status_map={f:status(v) for f,v in fields.items()}
    material=["entry_day","entry_action","adjustment_day","adjustment_action","exit_day","strike_reference","stop_reference","target_reference"]
    manual=any(status_map[f] in {"UNSPECIFIED","CONFLICTING"} for f in material)
    return {"video_id":video_id,"title":title,"source_url":url,"segment_count":len(segments),"family_hits":family_hits(full),"fields":fields,"field_status":status_map,"requires_manual_review":manual,"retrieved_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}

def load_csv(path):
    with path.open(encoding="utf-8",newline="") as fh: return list(csv.DictReader(fh))

def main():
    root=Path("data/equity_income"); videos=load_csv(root/"video_inventory.csv")
    candidates=[v for v in videos if v.get("candidate_payoff_family")!="unclassified"]
    out=root/"phase27_1_rule_evidence.jsonl"; rows=[]
    for v in candidates:
        try: rows.append(build(v["video_id"],v.get("title",""),v.get("webpage_url",""),fetch(v["video_id"])))
        except Exception as exc: rows.append({"video_id":v["video_id"],"title":v.get("title",""),"status":"ERROR","error":repr(exc)})
    out.write_text("".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in rows),encoding="utf-8")
    summary={"candidate_videos":len(candidates),"processed":sum("status" not in r for r in rows),"errors":sum(r.get("status")=="ERROR" for r in rows),"manual_review_required":sum(bool(r.get("requires_manual_review")) for r in rows),"conflicting_records":sum(any(v=="CONFLICTING" for v in r.get("field_status",{}).values()) for r in rows)}
    (root/"phase27_1_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__": main()
