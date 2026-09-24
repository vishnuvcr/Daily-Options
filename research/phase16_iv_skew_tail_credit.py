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
      SELECT CAST(datetime AS TIMESTAMP) datetime,
             CAST(CAST(datetime AS TIMESTAMP)+INTERVAL '5 hours 30 minutes' AS DATE) trade_date,
             expiry_type,
             option_type,
             strike_type,
             CAST(spot AS DOUBLE) spot,
             CAST(iv AS DOUBLE) iv
      FROM read_parquet({g}, union_by_name=true)
      WHERE close>0 AND iv BETWEEN 0 AND 300
        AND STRFTIME(CAST(datetime AS TIMESTAMP)+INTERVAL '5 hours 30 minutes','%H:%M:%S')
            BETWEEN '09:30:00' AND '10:30:00'
    ),
    nb AS (
      SELECT *
      FROM b
    ),
    m AS (
      SELECT datetime, trade_date, expiry_type, MAX(spot) spot,
        AVG(CASE WHEN option_type='PUT' AND strike_type='ATM-2' THEN iv END) put_iv,
        AVG(CASE WHEN option_type='CALL' AND strike_type='ATM+2' THEN iv END) call_iv
      FROM nb
      GROUP BY datetime, trade_date, expiry_type
    ),
    dense AS (
      SELECT *,
        spot/LAG(spot,15) OVER(PARTITION BY trade_date ORDER BY datetime)-1 ret15
      FROM m
    )
    SELECT *,
      put_iv-call_iv skew_iv
    FROM dense
    WHERE put_iv IS NOT NULL AND call_iv IS NOT NULL
      AND ret15 IS NOT NULL
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

def clip_hold_window(m, entry_time, hold_minutes):
    end_time=pd.Timestamp(entry_time)+pd.Timedelta(minutes=int(hold_minutes))
    return m[(m['datetime']>=pd.Timestamp(entry_time)) & (m['datetime']<=end_time)].copy()

def lot(d):
    d=pd.Timestamp(d).date()
    if d<pd.Timestamp('2024-04-26').date():return 50
    if d<pd.Timestamp('2024-11-21').date():return 25
    if d<pd.Timestamp('2026-01-06').date():return 75
    return 65

def run(root,out,slippage,expiry):
    feat=load_features(root,expiry)
    vs=variant_grid(expiry)
    out.mkdir(parents=True,exist_ok=True)
    if feat.empty:
        t=pd.DataFrame()
        t.to_csv(out/'phase16_trades.csv',index=False)
        s={'expiry_type':expiry,'variants':len(vs),'feature_rows':0,'trade_rows':0,'positive_variants':0,'target_qualified':0,'best':None,'slippage':slippage}
        (out/'phase16_summary.json').write_text(json.dumps(s,indent=2,default=str))
        print(json.dumps(s,indent=2,default=str))
        return s

    signal_sets=[]
    for v in vs:
        ss=signals(feat,v).copy()
        if not ss.empty:
            ss['variant_id']=f"{v['entry_time']}|z{v['z']}|j{v['jump']}|w{v['width']}|{v['side']}|h{v['hold']}|s{v['stop']}"
            signal_sets.append(ss[['trade_date','datetime','expiry_type','variant_id','skew_z']])
    sig_all=pd.concat(signal_sets,ignore_index=True) if signal_sets else pd.DataFrame()
    if sig_all.empty:
        t=pd.DataFrame()
        t.to_csv(out/'phase16_trades.csv',index=False)
        s={'expiry_type':expiry,'variants':len(vs),'feature_rows':len(feat),'trade_rows':0,'positive_variants':0,'target_qualified':0,'best':None,'slippage':slippage}
        (out/'phase16_summary.json').write_text(json.dumps(s,indent=2,default=str))
        print(json.dumps(s,indent=2,default=str))
        return s

    wanted=sig_all[['trade_date','datetime','expiry_type']].drop_duplicates().copy()
    wanted['entry_time']=pd.to_datetime(wanted.datetime)+pd.Timedelta(minutes=1)

    g=files(root,expiry)
    con=duckdb.connect()
    con.register('wanted',wanted[['trade_date','expiry_type','entry_time']])
    q=f"""
    SELECT CAST(o.datetime AS TIMESTAMP) datetime,
           o.expiry_type, o.option_type, o.strike_type,
           CAST(o.strike_price AS DOUBLE) strike,
           CAST(o.open AS DOUBLE) open
    FROM read_parquet({g},union_by_name=true) o
    JOIN wanted w
      ON o.expiry_type=w.expiry_type
     AND CAST(o.datetime AS TIMESTAMP)=w.entry_time
     AND CAST(CAST(o.datetime AS TIMESTAMP)+INTERVAL '5 hours 30 minutes' AS DATE)=w.trade_date
    WHERE o.close>0
    """
    entry=con.execute(q).df()

    setup_rows=[]
    for key,ss in sig_all.groupby(['trade_date','datetime','expiry_type'],sort=False):
        d,dt,ex=key
        et=pd.Timestamp(dt)+pd.Timedelta(minutes=1)
        e=entry[(entry.datetime==et)&(entry.expiry_type==ex)]
        if e.empty: continue
        for side in ('PUT','CALL'):
            short_type='ATM-2' if side=='PUT' else 'ATM+2'
            sh=e[(e.option_type==side)&(e.strike_type==short_type)]
            if sh.empty: continue
            short=sh.iloc[0]
            for width in WIDTHS:
                wing_type=('ATM-'+str(2+width)) if side=='PUT' else ('ATM+'+str(2+width))
                wh=e[(e.option_type==side)&(e.strike_type==wing_type)]
                if wh.empty: continue
                wing=wh.iloc[0]
                credit=float(short.open-wing.open)
                if credit>0:
                    setup_rows.append({'trade_date':d,'entry_time':et,'expiry_type':ex,'side':side,'width':width,
                                       'short_strike':float(short.strike),'wing_strike':float(wing.strike),
                                       'short_entry':float(short.open),'wing_entry':float(wing.open),'credit':credit})
    con.close()

    setup_df=pd.DataFrame(setup_rows).drop_duplicates()
    if setup_df.empty:
        t=pd.DataFrame()
        t.to_csv(out/'phase16_trades.csv',index=False)
        s={'expiry_type':expiry,'variants':len(vs),'feature_rows':len(feat),'signal_rows':len(sig_all),'setup_rows':0,'trade_rows':0,'positive_variants':0,'target_qualified':0,'best':None,'slippage':slippage}
        (out/'phase16_summary.json').write_text(json.dumps(s,indent=2,default=str))
        print(json.dumps(s,indent=2,default=str))
        return s

    con=duckdb.connect()
    con.register('legs',setup_df[['trade_date','entry_time','expiry_type','side','short_strike','wing_strike']].drop_duplicates())
    q2=f"""
    SELECT CAST(o.datetime AS TIMESTAMP) datetime,
           o.expiry_type, o.option_type,
           CAST(o.strike_price AS DOUBLE) strike,
           CAST(o.high AS DOUBLE) high,
           CAST(o.low AS DOUBLE) low,
           CAST(o.close AS DOUBLE) close_px,
           l.trade_date AS trade_date,
           l.entry_time AS entry_time,
           l.side AS side,
           l.short_strike AS short_strike,
           l.wing_strike AS wing_strike
    FROM read_parquet({g},union_by_name=true) o
    JOIN legs l
      ON o.expiry_type=l.expiry_type
     AND o.option_type=l.side
     AND CAST(o.strike_price AS DOUBLE) IN (l.short_strike,l.wing_strike)
     AND CAST(o.datetime AS TIMESTAMP)>=l.entry_time
     AND CAST(o.datetime AS TIMESTAMP)<=l.entry_time+INTERVAL '60 minutes'
     AND CAST(CAST(o.datetime AS TIMESTAMP)+INTERVAL '5 hours 30 minutes' AS DATE)=l.trade_date
    WHERE o.close>0
    """
    win=con.execute(q2).df()
    con.close()
    if not win.empty:
        win['datetime']=pd.to_datetime(win['datetime']).dt.floor('min')
        win['entry_time']=pd.to_datetime(win['entry_time']).dt.floor('min')
        win['trade_date']=pd.to_datetime(win['trade_date']).dt.date
        win['expiry_type']=win['expiry_type'].astype(str)
        win['side']=win['side'].astype(str)

    setup_df['entry_time']=pd.to_datetime(setup_df['entry_time']).dt.floor('min')
    setup_df['trade_date']=pd.to_datetime(setup_df['trade_date']).dt.date
        setup_df['expiry_type']=setup_df['expiry_type'].astype(str)
    setup_df['side']=setup_df['side'].astype(str)

    outcome_rows=[]
    setup_index=setup_df.set_index(['trade_date','entry_time','expiry_type','side','width'])
    for key,u in setup_index.iterrows():
        d,et,ex,side,width=key
        q=win[(win.trade_date==d)&(win.entry_time==et)&(win.expiry_type==ex)&(win.side==side)&(win.short_strike==u.short_strike)&(win.wing_strike==u.wing_strike)]
        if q.empty: continue
        a=q[q.strike==u.short_strike][['datetime','high','low','close_px']].rename(columns={'high':'shigh','low':'slow','close_px':'sclose'})
        b=q[q.strike==u.wing_strike][['datetime','high','low','close_px']].rename(columns={'high':'whigh','low':'wlow','close_px':'wclose'})
        m=a.merge(b,on='datetime').sort_values('datetime')
        if m.empty: continue
        for hold in HOLDS:
            mm=m[m.datetime<=et+pd.Timedelta(minutes=hold)]
            if mm.empty: continue
            hi=mm.shigh-mm.wlow
            lo=mm.slow-mm.whigh
            for stop in STOPS:
                stopv=u.credit*stop
                target=u.credit*TARGET_RATIO
                si=np.flatnonzero(hi>=stopv)
                ti=np.flatnonzero(lo<=target)
                si=int(si[0]) if len(si) else 10**9
                ti=int(ti[0]) if len(ti) else 10**9
                if si<=ti and si<10**9: ix,reason=si,'STOP'
                elif ti<10**9: ix,reason=ti,'TARGET'
                else: ix,reason=len(mm)-1,'TIME'
                exrow=mm.iloc[ix]
                net=OptionCostModel().vertical_credit_spread_net_pnl(float(u.short_entry),float(u.wing_entry),float(exrow.sclose),float(exrow.wclose),lot(d),slippage_points=slippage)
                outcome_rows.append({
                    'trade_date':d,'datetime':et-pd.Timedelta(minutes=1),'expiry_type':ex,
                    'side':side,'width':width,'hold':hold,'stop':stop,
                    'net_pnl':net,'reason':reason,'entry_credit':float(u.credit)
                })
    outcomes=pd.DataFrame(outcome_rows)

    rows=[]
    if not outcomes.empty:
        for v in vs:
            ss=signals(feat,v).copy()
            if ss.empty: continue
            keycols=['trade_date','datetime','expiry_type']
            oo=outcomes[
                outcomes.side.eq(v['side']) &
                outcomes.width.eq(v['width']) &
                outcomes.hold.eq(v['hold']) &
                outcomes.stop.eq(v['stop'])
            ]
            if oo.empty: continue
            merged=ss.merge(oo,on=keycols,how='inner')
            if not merged.empty:
                merged['variant_id']=f"{v['entry_time']}|z{v['z']}|j{v['jump']}|w{v['width']}|{v['side']}|h{v['hold']}|s{v['stop']}"
                rows.append(merged[['trade_date','variant_id','net_pnl','reason','skew_z','entry_credit']])

    t=pd.DataFrame(rows)
    t.to_csv(out/'phase16_trades.csv',index=False)
    board=[]
    if not t.empty:
        days=feat.trade_date.nunique()
        for vid,g2 in t.groupby('variant_id'):
            d=g2.groupby('trade_date').net_pnl.sum()
            pos=g2.loc[g2.net_pnl>0,'net_pnl'].sum()
            neg=-g2.loc[g2.net_pnl<0,'net_pnl'].sum()
            board.append({'variant_id':vid,'trades':len(g2),'active_days':len(d),'mean_active_day_net':d.mean(),'mean_all_day_net':g2.net_pnl.sum()/max(1,days),'win_rate':(g2.net_pnl>0).mean(),'profit_factor':pos/max(1e-9,neg),'max_drawdown':(d.cumsum()-d.cumsum().cummax()).min(),'total_net':g2.net_pnl.sum()})
    b=pd.DataFrame(board).sort_values('mean_all_day_net',ascending=False) if board else pd.DataFrame()
    b.to_csv(out/'phase16_leaderboard.csv',index=False)
    s={'expiry_type':expiry,'variants':len(vs),'feature_rows':len(feat),'signal_rows':len(sig_all),'setup_rows':len(setup_df),'window_rows':len(win),'trade_rows':len(t),'positive_variants':int((b.mean_all_day_net>0).sum()) if not b.empty else 0,'target_qualified':int((b.mean_active_day_net>=1000).sum()) if not b.empty else 0,
        'target_metric':'mean_active_day_net','best':b.iloc[0].to_dict() if not b.empty else None,'slippage':slippage}
    (out/'phase16_summary.json').write_text(json.dumps(s,indent=2,default=str))
    print(json.dumps(s,indent=2,default=str))
    return s

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--data',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--slippage',type=float,default=.2); ap.add_argument('--expiry-type',choices=['WEEK','MONTH'],required=True); a=ap.parse_args(); run(a.data,a.out,a.slippage,a.expiry_type)