#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path

VIDEO_ID="6_W4UpFsehs"
URL=f"https://www.youtube.com/watch?v={VIDEO_ID}"
TERMS=["diagonal","calendar","low vix","vix","expiry","strike","premium","debit","credit","adjust","adjustment","stop","stop loss","target","profit","exit","lot","time","nifty","banknifty"]

def run(cmd,cwd=None):
    return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,check=False)

def clean_vtt(text):
    out=[]; seen=set()
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith("WEBVTT") or "-->" in line or line.startswith(("NOTE","STYLE","Kind:","Language:")): continue
        line=re.sub(r"<[^>]+>","",line)
        line=re.sub(r"&amp;","&",line)
        if line and line not in seen:
            seen.add(line); out.append(line)
    return "\n".join(out)

def ts_seconds(ts):
    h,m,s=ts.split(":"); return float(h)*3600+float(m)*60+float(s.replace(",", "."))

def parse_vtt(text):
    rows=[]; pending=None
    lines=text.splitlines()
    for i,line in enumerate(lines):
        if "-->" in line:
            a=line.split("-->")[0].strip()
            try: pending=ts_seconds(a)
            except: pending=None
        elif pending is not None and line.strip() and not line.startswith(("WEBVTT","NOTE","STYLE")):
            t=re.sub(r"<[^>]+>","",line.strip())
            if t:
                rows.append({"start_sec":pending,"text":t})
            pending=None
    return rows

def acquire(out):
    out.mkdir(parents=True,exist_ok=True)
    r=run(["yt-dlp","--skip-download","--write-auto-subs","--write-subs","--sub-langs","en.*,hi.*","--sub-format","vtt","--print","%(id)s\t%(title)s\t%(upload_date)s","-o",str(out/"%(id)s.%(ext)s"),URL])
    meta={"video_id":VIDEO_ID,"url":URL,"command_returncode":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
    (out/"acquisition.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    vtts=list(out.glob("*.vtt"))
    if not vtts: raise RuntimeError("No VTT caption track was acquired")
    primary=max(vtts,key=lambda p:p.stat().st_size)
    raw=primary.read_text(encoding="utf-8",errors="replace")
    (out/"raw.vtt").write_text(raw,encoding="utf-8")
    norm=clean_vtt(raw); (out/"normalized.txt").write_text(norm,encoding="utf-8")
    evidence=parse_vtt(raw)
    windows=[]
    for i,row in enumerate(evidence):
        lo=max(0,i-4); hi=min(len(evidence),i+5)
        low=row["text"].lower()
        if any(t in low for t in TERMS):
            windows.append({"start_sec":row["start_sec"],"term_hits":[t for t in TERMS if t in low],"context":evidence[lo:hi]})
    result={"video_id":VIDEO_ID,"title":"Retail Option Seller's Diagonal Setup for Low Vix","source_url":URL,
            "caption_file":primary.name,"raw_sha256":hashlib.sha256(raw.encode()).hexdigest(),
            "normalized_sha256":hashlib.sha256(norm.encode()).hexdigest(),
            "caption_rows":len(evidence),"windows":windows[:500],
            "field_requirements":["underlying","structure","expiry","entry_day","entry_time","strike_rule","premium_rule","ratio","low_vix_condition","adjustment_trigger","adjustment_action","stop","target","exit","capital"],
            "status":"SOURCE_REVIEW_REQUIRED"}
    (out/"source_resolution.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,required=True)
    print(json.dumps(acquire(ap.out),indent=2))
