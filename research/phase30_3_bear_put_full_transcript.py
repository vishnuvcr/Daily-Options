#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

import requests

VIDEO_ID="IpCuGEDxF1k"
URL="https://youtubegpt.ai/api/transcript"

TERMS=[
    "bear put spread","buy","sell","put","resistance","support","break",
    "crack","gap","gap up","gap down","adjust","adjustment","ratio",
    "square off","reverse","stop loss","stop-loss","target","profit",
    "expiry","weekly","Tuesday","Thursday","Wednesday","Monday","Friday",
    "strike","premium","debit","credit","margin","capital","lot","lots",
    "roll","hold","entry","exit","enter","leave"
]

def norm(x):
    return re.sub(r"\s+"," ",str(x or "")).strip()

def fetch():
    r=requests.get(URL,params={"v":VIDEO_ID,"format":"json","lang":"en"},
                   headers={"User-Agent":"Daily-Options-Phase30.3/2.0"},timeout=(5,30))
    r.raise_for_status()
    data=r.json()
    if not data.get("ok"):
        raise RuntimeError(str(data))
    segs=[s for s in data.get("segments",[]) if norm(s.get("text"))]
    if not segs:
        raise RuntimeError("EMPTY_TRANSCRIPT")
    return segs,data

def contexts(segs,radius=10):
    out=[]
    for i,s in enumerate(segs):
        txt=norm(s["text"])
        if not any(re.search(re.escape(term),txt,re.I) for term in TERMS):
            continue
        lo=max(0,i-radius); hi=min(len(segs),i+radius+1)
        out.append({
            "anchor_start_ms":int(float(s.get("start") or 0)),
            "anchor_text":txt,
            "context":[
                {"start_ms":int(float(segs[j].get("start") or 0)),"text":norm(segs[j].get("text"))}
                for j in range(lo,hi)
            ],
        })
    return out

def main():
    segs,raw=fetch()
    text=" ".join(norm(s["text"]) for s in segs)
    result={
        "video_id":VIDEO_ID,
        "source_url":f"https://www.youtube.com/watch?v={VIDEO_ID}",
        "segment_count":len(segs),
        "retrieved_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        "transcript_text_sha256":hashlib.sha256(text.encode()).hexdigest(),
        "segments":segs,
        "keyword_contexts":contexts(segs,10),
        "backtest_allowed":False,
    }
    Path("reports").mkdir(parents=True,exist_ok=True)
    Path("reports/phase30_3_bear_put_full_transcript.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "video_id":VIDEO_ID,
        "segment_count":len(segs),
        "sha256":result["transcript_text_sha256"],
        "contexts":len(result["keyword_contexts"]),
        "backtest_allowed":False,
    },indent=2))

if __name__=="__main__":
    main()
