#!/usr/bin/env python3
"""Phase 27.6: targeted source-context extraction for the aRj Air Defense candidate.

No transcript text is persisted. The runner returns only structured facts,
timestamps and hashes needed to decide whether the rule is complete enough
for a future backtest.
"""
from __future__ import annotations
import hashlib,json,re,time
from pathlib import Path
import requests

VIDEO_ID='aRjY_O6U3nQ'

def fetch_segments():
    r=requests.get('https://youtubegpt.ai/api/transcript',params={'v':VIDEO_ID,'format':'json','lang':'en'},headers={'User-Agent':'Daily-Options-Phase27.6/1.0'},timeout=(5,20))
    r.raise_for_status(); d=r.json()
    if not d.get('ok'): raise RuntimeError(str(d.get('message') or d.get('code') or 'API_NOT_OK'))
    segs=[s for s in (d.get('segments') or []) if isinstance(s,dict) and str(s.get('text') or '').strip()]
    return segs

def ctx(segs,i,r=3):
    lo=max(0,i-r); hi=min(len(segs),i+r+1)
    return ' '.join(str(segs[j].get('text') or '') for j in range(lo,hi))

def pick(segs, patterns, value_pattern=None, limit=20):
    out=[]
    for i,s in enumerate(segs):
        c=ctx(segs,i)
        for pat in patterns:
            for m in re.finditer(pat,c,re.I):
                if value_pattern:
                    vm=re.search(value_pattern,m.group(0),re.I)
                    value=vm.group(1) if vm and vm.lastindex else m.group(0)
                else:
                    value=m.group(1) if m.lastindex else m.group(0)
                out.append({'value':re.sub(r'\s+',' ',value).strip()[:120],'start_sec':round(float(s.get('start') or 0),1)})
                if len(out)>=limit: return out
    # stable unique
    seen=set(); uniq=[]
    for x in out:
        k=(x['value'].lower(),x['start_sec'])
        if k not in seen: seen.add(k); uniq.append(x)
    return uniq[:limit]

def main():
    segs=fetch_segments()
    facts={
      'expiry_day_context':pick(segs,[r'\bexpiry day\b',r'\bweekly expiry\b',r'\bexpiry-day\b']),
      'entry_context':pick(segs,[r'\b(?:entry|enter|start the trade|take the trade)\b[^.!?]{0,120}',r'\b(?:sell|short)\b[^.!?]{0,120}\b(?:strangle|call|put|option)\b']),
      'expiry_timing':pick(segs,[r'\b\d+\s*minutes?\s*(?:before|to)\s*(?:expiry|expiration)\b',r'\b\d{1,2}:\d{2}\s*(?:am|pm)?\b[^.!?]{0,80}(?:expiry|exit|close)']),
      'delta':pick(segs,[r'\b(0?\.\d+|\d+(?:\.\d+)?)\s*(?:delta|Δ)\b'],limit=20),
      'strike':pick(segs,[r'\b(?:out of the money|OTM|ATM|at the money)\b',r'\bone strike\b',r'\bshort strike\b',r'\bshort strikes\b']),
      'adjustment_trigger':pick(segs,[r'\b(?:adjust|adjustment)\b[^.!?]{0,120}',r'\b(?:when price|price)\b[^.!?]{0,120}\b(?:short strike|short strikes|approach|near)\b']),
      'adjustment_action':pick(segs,[r'\b(?:add|hedge|move|roll|widen|narrow)\b[^.!?]{0,100}']),
      'stop':pick(segs,[r'\b(?:stop loss|stop-loss|hard stop|soft stop|SL)\b[^.!?]{0,120}',r'\b(?:loss)\b[^.!?]{0,60}\b(?:percent|%)\b']),
      'target':pick(segs,[r'\b(?:target|take profit|book profit|profit target)\b[^.!?]{0,120}']),
      'structure':pick(segs,[r'\b(?:short strangle|iron condor|ratio spread|jade lizard|strangle|condor)\b']),
      'time_refs':pick(segs,[r'\b(?:at|around)\s+\d{1,2}:\d{2}\b',r'\b\d{1,2}:\d{2}\b']),
    }
    summary={
      'video_id':VIDEO_ID,
      'segment_count':len(segs),
      'transcript_text_sha256':hashlib.sha256(' '.join(str(s.get('text') or '') for s in segs).encode()).hexdigest(),
      'facts':facts,
      'external_corroboration':{
        'source_url':'https://www.youtube.com/watch?v=aRjY_O6U3nQ',
        'claims':['India VIX and time-to-expiry expected-range framework','1-sigma and 2-sigma ranges','short strangles/iron condors','adjustments when price approaches short strikes'],
      },
      'backtest_allowed':False,
      'retrieved_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    }
    Path('reports/phase27_6_aRj_deep_dive.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:len(v) for k,v in facts.items()},sort_keys=True))

if __name__=='__main__': main()
