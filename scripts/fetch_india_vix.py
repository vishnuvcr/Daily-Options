#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import requests

NSE_HOME = 'https://www.nseindia.com/'
VIX_URL = 'https://www.nseindia.com/api/historicalOR/vixhistory'
NIFTYINDICES_URL = 'https://www.niftyindices.com/Backpage.aspx/BindHistoricalIndiaVixData'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/136 Safari/537.36',
    'Accept': 'application/json,text/plain,*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/reports-indices-historical-vix',
    'Origin': 'https://www.nseindia.com',
}

def chunks(start, end, days=85):
    cur = start
    while cur <= end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)

def parse_rows(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ('data', 'records', 'rows'):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []

def normalize(df):
    mapping = {}
    for c in df.columns:
        k = str(c).strip().lower().replace(' ', '').replace('_', '')
        if k in ('date','tradedate','timestamp','eodtimestamp'):
            mapping[c] = 'date'
        elif k in ('close','closeprice','vix','indexclose','closeindex','closevalue','eodcloseindexval'):
            mapping[c] = 'close'
    df = df.rename(columns=mapping)
    if 'date' not in df.columns or 'close' not in df.columns:
        raise RuntimeError(f'Unexpected NSE India VIX schema: {list(df.columns)}')
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce').dt.date
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df = df.dropna(subset=['date','close']).drop_duplicates('date').sort_values('date')
    return df[['date','close']]

def fetch_one(session, start, end):
    last = None
    for attempt in range(3):
        try:
            r = session.get(
                VIX_URL,
                params={'from': start.strftime('%d-%m-%Y'), 'to': end.strftime('%d-%m-%Y')},
                headers=HEADERS, timeout=(15, 45),
            )
            if r.status_code < 400:
                rows = parse_rows(r.json())
                if rows:
                    return rows
            last = RuntimeError(f'NSE endpoint status={r.status_code}')
            last = RuntimeError('empty NSE response')
        except Exception as exc:
            last = exc
        time.sleep(2 ** attempt)
    # Fallback: NSE Indices public historical VIX service documented by its Python client ecosystem.
    body = "{'name':'India VIX','startDate':'%s','endDate':'%s'}" % (start.strftime('%d %b %Y'), end.strftime('%d %b %Y'))
    h = dict(HEADERS)
    h.update({'Content-Type':'application/json; charset=utf-8','Referer':'https://www.niftyindices.com/reports/historical-data','Origin':'https://www.niftyindices.com'})
    for attempt in range(4):
        try:
            r = session.post(NIFTYINDICES_URL, data=body, headers=h, timeout=(15,45))
            r.raise_for_status()
            outer = r.json()
            inner = outer.get('d','[]') if isinstance(outer,dict) else outer
            if isinstance(inner,str):
                if inner.lower() == 'false':
                    raise RuntimeError('NiftyIndices returned false')
                inner = json.loads(inner)
            rows = inner if isinstance(inner,list) else []
            if rows:
                return rows
            last = RuntimeError('empty NiftyIndices fallback response')
        except Exception as exc:
            last = exc
        time.sleep(2 ** attempt)
    raise RuntimeError(f'India VIX fetch failed for both NSE endpoints {start}..{end}: {last}')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True)
    ap.add_argument('--end', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    session = requests.Session()
    session.headers.update(HEADERS)
    rows = []
    for a, b in chunks(start, end):
        rows.extend(fetch_one(session, a, b))
    df = normalize(pd.DataFrame(rows))
    if len(df) < 100:
        raise RuntimeError(f'Suspicious India VIX row count: {len(df)}')
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    meta = {'source':'NSE India historical India VIX', 'endpoint':VIX_URL, 'rows':len(df), 'start':str(df['date'].min()), 'end':str(df['date'].max())}
    out.with_suffix('.meta.json').write_text(json.dumps(meta, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(meta, indent=2))

if __name__ == '__main__':
    main()
