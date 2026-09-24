from __future__ import annotations
import argparse,json
from pathlib import Path
import duckdb,numpy as np,pandas as pd
from research.cost_model import OptionCostModel

ENTRY_TIMES=('09:45:00','10:00:00','10:15:00')
SKEW_Z=(1.0,1.5,2.0)
JUMP_MAX=(0.0025,0.0040)
WIDTHS=(1,2)
HOLDS=(30,60)
STOPS=(1.5,2.0)
TARGET_RATIO=0.5

def files(root,expiry):
    names=[]
    for k in (2,3,4): names += [f'ATM+{k}_CE.parquet',f'ATM+{k}_PE.parquet',f'ATM-{k}_CE.parquet',f'ATM-{k}_PE.parquet']
    ps=[str(root/expiry/n) for n in names]
    miss=[p for p in ps if not Path(p).exists()]
    if miss: raise FileNotFoundError(','.join(miss))
    return '['+','.join(repr(p) for p in ps)+']'

def feature_query(root, expiry_type):
    g=files(root, expiry_type)
    times=','.join(repr(x) for x in ENTRY_TIMES)
    return f'''
    WITH b AS (
      SELECT CAST(datetime AS TIMESTAMP) datetime, CAST(date AS DATE) trade_date, expiry_type,
             option_type, strike_type, CAST(spot AS DOUBLE) spot, CAST(iv AS DOUBLE) iv
      FROM read_parquet({g}, union_by_name=true)
      WHERE close>0 AND iv BETWEEN 0 AND 300
        AND STRFTIME(CAST(datetime AS TIMESTAMP)+INTERVAL '5 hours 30 minutes','%H:%M:%S') BETWEEN '09:30:00' AND '10:30:00'
    ),
    m AS (
      SELECT datetime, trade_date, expiry_type, MAX(spot) spot,
        AVG(CASE WHEN option_type='PUT' AND strike_type='ATM-2' THEN iv END) put_iv,
        AVG(CASE WHEN option_type='CALL' AND strike_type='ATM+2' THEN iv END) call_iv
      FROM b
      GROUP BY datetime, trade_date, expiry_type
    )
    SELECT *, put_iv-call_iv skew_iv,
      spot/LAG(spot,15) OVER(PARTITION BY trade_date ORDER BY datetime)-1 ret15
    FROM m
    WHERE put_iv IS NOT NULL AND call_iv IS NOT NULL
      AND STRFTIME(datetime+INTERVAL '5 hours 30 minutes','%H:%M:%S') IN ({times})
    ORDER BY trade_date, datetime
    '''


def load_features(root,expiry):
    q=feature_query(root,expiry)
    con=duckdb.connect()
    x=con.execute(q).df()
    con.close()
    if x.empty:return x
    x['trade_date']=pd.to_datetime(x.trade_date).dt.date
    x['datetime']=pd.to_datetime(x.datetime)
    x['ist_time']=(x['datetime']+pd.Timedelta(hours=5,minutes=30)).dt.strftime('%H:%M:%S')
    x=x.sort_values(['ist_time','trade_date','datetime'])
    g=x.groupby('ist_time')
    x['skew_mean']=g.skew_iv.transform(lambda s:s.shift(1).rolling(20,min_periods=10).mean())
    x['skew_std']=g.skew_iv.transform(lambda s:s.shift(1).rolling(20,min_periods=10).std())
    x['skew_z']=(x.skew_iv-x.skew_mean)/x.skew_std.replace(0,np.nan)
    return x.dropna(subset=['skew_z','ret15'])

def variant_grid(expiry):
    return [dict(entry_time=e,z=z,jump=j,width=w,hold=h,stop=s,side=side,expiry_type=expiry)
            for e in ENTRY_TIMES for z in SKEW_Z for j in JUMP_MAX for w in WIDTHS for h in HOLDS for s in STOPS for side in ('PUT','CALL')]

def signals(feat,v):
    m=(feat.ist_time==v['entry_time'])&(feat.skew_z.abs()>=v['z'])&(feat.ret15.abs()<=v['jump'])
    m &= feat.skew_z.ge(v['z']) if v['side']=='PUT' else feat.skew_z.le(-v['z'])
    return feat.loc[m].sort_values('datetime').drop_duplicates(['trade_date','expiry_type'])

def lot(d):
    d=pd.Timestamp(d).date()
    if d<pd.Timestamp('2024-04-26').date():return 50
    if d<pd.Timestamp('2024-11-21').date():return 25
    if d<pd.Timestamp('2026-01-06').date():return 75
    return 65

def run(root,out,slippage,expiry):
    feat=load_features(root,expiry); vs=variant_grid(expiry); rows=[]
    g=files(root,expiry)
    con=duckdb.connect()
    q=f'''SELECT CAST(datetime AS TIMESTAMP) datetime,expiry_type,option_type,strike_type,CAST(strike_price AS DOUBLE) strike,
      CAST(open AS DOUBLE) open,CAST(high AS DOUBLE) high,CAST(low AS DOUBLE) low,CAST(close AS DOUBLE) AS close_px
      FROM read_parquet({g},union_by_name=true) WHERE close>0
      AND STRFTIME(CAST(datetime AS TIMESTAMP)+INTERVAL '5 hours 30 minutes','%H:%M:%S') IN ('09:46:00','10:01:00','10:16:00')'''
    entry=con.execute(q).df()
    q2=f'''SELECT CAST(datetime AS TIMESTAMP) datetime,expiry_type,option_type,CAST(strike_price AS DOUBLE) strike,
      CAST(open AS DOUBLE) open,CAST(high AS DOUBLE) high,CAST(low AS DOUBLE) low,CAST(close AS DOUBLE) AS close_px
      FROM read_parquet({g},union_by_name=true) WHERE close>0'''
    win=con.execute(q2).df(); con.close()
    for v in vs:
        s=signals(feat,v)
        for _,r in s.iterrows():
            et=r.datetime+pd.Timedelta(minutes=1); side=v['side']; short_type='ATM-2' if side=='PUT' else 'ATM+2'; wing_type=('ATM-'+str(2+v['width'])) if side=='PUT' else ('ATM+'+str(2+v['width']))
            e=entry[(entry.datetime==et)&(entry.option_type==side)&(entry.strike_type.isin([short_type,wing_type]))]
            if e.empty: continue
            sh=e[e.strike_type==short_type]; wh=e[e.strike_type==wing_type]
            if sh.empty or wh.empty: continue
            short=sh.iloc[0]; wing=wh.iloc[0]; credit=float(short.open-wing.open)
            if credit<=0: continue
            end=et+pd.Timedelta(minutes=v['hold']); q=win[(win.datetime>=et)&(win.datetime<=end)&(win.option_type==side)&(win.strike.isin([float(short.strike),float(wing.strike)]))]
            if q.empty: continue
            a=q[q.strike==float(short.strike)][['datetime','high','low','close_px']].rename(columns={'high':'shigh','low':'slow','close_px':'sclose'})
            b=q[q.strike==float(wing.strike)][['datetime','high','low','close_px']].rename(columns={'high':'whigh','low':'wlow','close_px':'wclose'})
            m=a.merge(b,on='datetime').sort_values('datetime')
            if m.empty: continue
            stop=credit*v['stop']; target=credit*TARGET_RATIO; hi=m.shigh-m.wlow; lo=m.slow-m.whigh; si=np.flatnonzero(hi>=stop); ti=np.flatnonzero(lo<=target); si=int(si[0]) if len(si) else 10**9; ti=int(ti[0]) if len(ti) else 10**9
            if si<=ti and si<10**9: ix,reason=si,'STOP'
            elif ti<10**9: ix,reason=ti,'TARGET'
            else: ix,reason=len(m)-1,'TIME'
            ex=m.iloc[ix]; net=OptionCostModel().vertical_credit_spread_net_pnl(float(short.open),float(wing.open),float(ex.sclose),float(ex.wclose),lot(r.trade_date),slippage_points=slippage)
            rows.append({'trade_date': r.trade_date, 'variant_id': f"{v['entry_time']}|z{v['z']}|j{v['jump']}|w{v['width']}|{side}|h{v['hold']}|s{v['stop']}", 'net_pnl': net, 'reason': reason, 'skew_z': float(r.skew_z), 'entry_credit': credit})
    t=pd.DataFrame(rows); out.mkdir(parents=True,exist_ok=True); t.to_csv(out/'phase16_trades.csv',index=False)
    board=[]
    if not t.empty:
        days=feat.trade_date.nunique()
        for vid,g in t.groupby('variant_id'):
            d=g.groupby('trade_date').net_pnl.sum(); pos=g.loc[g.net_pnl>0,'net_pnl'].sum(); neg=-g.loc[g.net_pnl<0,'net_pnl'].sum()
            board.append({'variant_id':vid,'trades':len(g),'active_days':len(d),'mean_active_day_net':d.mean(),'mean_all_day_net':g.net_pnl.sum()/max(1,days),'win_rate':(g.net_pnl>0).mean(),'profit_factor':pos/max(1e-9,neg),'max_drawdown':(d.cumsum()-d.cumsum().cummax()).min(),'total_net':g.net_pnl.sum()})
    b=pd.DataFrame(board).sort_values('mean_all_day_net',ascending=False) if board else pd.DataFrame(); b.to_csv(out/'phase16_leaderboard.csv',index=False)
    s={'expiry_type':expiry,'variants':len(vs),'feature_rows':len(feat),'trade_rows':len(t),'positive_variants':int((b.mean_all_day_net>0).sum()) if not b.empty else 0,'target_qualified':int((b.mean_all_day_net>=TARGET).sum()) if not b.empty else 0,'best':b.iloc[0].to_dict() if not b.empty else None,'slippage':slippage}
    (out/'phase16_summary.json').write_text(json.dumps(s,indent=2,default=str)); print(json.dumps(s,indent=2,default=str)); return s

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--data',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--slippage',type=float,default=.2); ap.add_argument('--expiry-type',choices=['WEEK','MONTH'],required=True); a=ap.parse_args(); run(a.data,a.out,a.slippage,a.expiry_type)