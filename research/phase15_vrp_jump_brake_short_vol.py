from __future__ import annotations
import argparse, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from research.cost_model import OptionCostModel
from research.phase10_contracts import index_option_lot_size

ENTRY_TIMES=('09:30:00','10:00:00','10:30:00')
VRP_THRESHOLDS=(0.0,2.0,4.0)
JUMP_MAX=(0.0025,0.0040)
STRUCTURES=('STRADDLE','IRONFLY')
EXPIRY_TYPES=('WEEK','MONTH')
HOLDS=(30,60)
STOP_RATIOS=(1.30,1.50)
TARGET_RATIO=0.50
TARGET=1000.0
VARIANT_COUNT=len(ENTRY_TIMES)*len(VRP_THRESHOLDS)*len(JUMP_MAX)*len(STRUCTURES)*len(EXPIRY_TYPES)*len(HOLDS)*len(STOP_RATIOS)

def parquet_glob(root: Path, expiry_type: str | None = None) -> str:
    if expiry_type:
        return (root / expiry_type / "*.parquet").as_posix()
    return (root / "**" / "*.parquet").as_posix()


def required_files_sql(root: Path, feature_only: bool = False, expiry_type: str | None = None) -> str:
    paths = []
    names = (
        ("ATM_CE.parquet", "ATM_PE.parquet")
        if feature_only else
        ("ATM_CE.parquet","ATM_PE.parquet","ATM+2_CE.parquet","ATM+2_PE.parquet","ATM-2_CE.parquet","ATM-2_PE.parquet")
    )
    expiry_types = (expiry_type,) if expiry_type else EXPIRY_TYPES
    for expiry_type in expiry_types:
        folder = root / expiry_type
        for name in names:
            p = folder / name
            paths.append(str(p))
    existing = [p for p in paths if Path(p).exists()]
    if len(existing) != len(paths):
        missing = sorted(set(paths) - set(existing))
        raise FileNotFoundError("Missing required Phase 15 strike files: " + ", ".join(missing))
    return "[" + ",".join(repr(p) for p in existing) + "]"

def feature_query(root:Path, expiry_type: str | None = None)->str:
    g=required_files_sql(root, feature_only=True, expiry_type=expiry_type); times=','.join(repr(x) for x in ENTRY_TIMES)
    return f'''
    WITH base AS (
      SELECT CAST(datetime AS TIMESTAMP) AS datetime, CAST(date AS DATE) AS trade_date, expiry_type, option_type, strike_type, CAST(spot AS DOUBLE) AS spot, CAST(iv AS DOUBLE) AS iv, CAST(close AS DOUBLE) AS close
      FROM read_parquet({g}, union_by_name=true)
      WHERE close>0
        AND option_type IN ('CALL','PUT')
        AND expiry_type IN ('WEEK','MONTH')
        AND STRFTIME(CAST(datetime AS TIMESTAMP) + INTERVAL '5 hours 30 minutes','%H:%M:%S') BETWEEN '09:00:00' AND '10:30:00'
    ),
    minute AS (
      SELECT datetime,trade_date,expiry_type,strike_type,MAX(spot) AS spot,
        AVG(CASE WHEN strike_type='ATM' AND option_type='CALL' AND iv BETWEEN 0 AND 300 THEN iv END) AS call_iv,
        AVG(CASE WHEN strike_type='ATM' AND option_type='PUT' AND iv BETWEEN 0 AND 300 THEN iv END) AS put_iv
      FROM base GROUP BY ALL
    ),
    lagged AS (
      SELECT *, spot/LAG(spot,15) OVER(PARTITION BY trade_date ORDER BY datetime)-1 AS ret15,
        LN(spot/LAG(spot) OVER(PARTITION BY trade_date ORDER BY datetime)) AS log_ret
      FROM minute
    ),
    rv AS (
      SELECT *, STDDEV_SAMP(log_ret) OVER(PARTITION BY trade_date ORDER BY datetime ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)*SQRT(252.0*375.0)*100.0 AS rv30
      FROM lagged
    )
    SELECT trade_date,datetime,expiry_type,spot,call_iv,put_iv,
      ((call_iv+put_iv)/2.0)-rv30 AS vrp,ABS(ret15) AS abs_ret15
    FROM rv
    WHERE STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') IN ({times})
      AND call_iv IS NOT NULL AND put_iv IS NOT NULL AND rv30 IS NOT NULL AND ret15 IS NOT NULL
    ORDER BY trade_date,datetime,expiry_type
    '''
def variant_grid():
    return [dict(entry_time=e,vrp_threshold=v,jump_max=j,structure=s,expiry_type=x,hold_minutes=h,stop_ratio=r)
            for e in ENTRY_TIMES for v in VRP_THRESHOLDS for j in JUMP_MAX for s in STRUCTURES for x in EXPIRY_TYPES for h in HOLDS for r in STOP_RATIOS]

def load_signal_rows(root, expiry_type=None):
    con=duckdb.connect(); out=con.execute(feature_query(root, expiry_type=expiry_type)).df(); con.close()
    if out.empty: return out
    out.trade_date=pd.to_datetime(out.trade_date).dt.date; out.datetime=pd.to_datetime(out.datetime)
    return out

def select_signals(features,variant):
    ist_time=(features.datetime + pd.Timedelta(hours=5, minutes=30)).dt.strftime('%H:%M:%S')
    m=ist_time.eq(variant['entry_time']) & features.vrp.ge(variant['vrp_threshold']) & features.abs_ret15.le(variant['jump_max']) & features.expiry_type.eq(variant['expiry_type'])
    x=features[m].copy()
    return x.sort_values(['trade_date','datetime']).drop_duplicates(['trade_date','expiry_type'])[['trade_date','datetime','expiry_type','spot','vrp','abs_ret15']]
def load_entry_quotes(root,signals):
    if signals.empty:
        return pd.DataFrame()

    wanted = signals[['trade_date','expiry_type','datetime']].drop_duplicates().copy()
    wanted['entry_time'] = wanted['datetime'] + pd.Timedelta(minutes=1)
    con = duckdb.connect()
    con.register('wanted', wanted[['trade_date','expiry_type','entry_time']])

    expiry_type = str(signals.expiry_type.iloc[0])
    g = required_files_sql(root, expiry_type=expiry_type)
    q = f'''
    SELECT
      CAST(o.datetime AS TIMESTAMP) AS datetime,
      o.expiry_type,
      o.option_type,
      o.strike_type,
      CAST(o.strike_price AS DOUBLE) AS strike,
      CAST(o.open AS DOUBLE) AS open,
      CAST(o.high AS DOUBLE) AS high,
      CAST(o.low AS DOUBLE) AS low,
      CAST(o.close AS DOUBLE) AS close,
      w.trade_date AS trade_date
    FROM read_parquet({g}, union_by_name=true) o
    JOIN wanted w
      ON o.expiry_type = w.expiry_type
     AND CAST(o.datetime AS TIMESTAMP) = w.entry_time
     AND CAST(CAST(o.datetime AS TIMESTAMP) + INTERVAL '5 hours 30 minutes' AS DATE) = w.trade_date
    WHERE o.close > 0
      AND o.option_type IN ('CALL','PUT')
    '''
    out = con.execute(q).df()
    con.close()
    if out.empty:
        return out
    out['datetime'] = pd.to_datetime(out['datetime']).dt.floor('min')
    out['trade_date'] = pd.to_datetime(out['trade_date']).dt.date
    return out

def load_execution_windows(root,setup_rows,max_hold=60):
    if setup_rows.empty:
        return pd.DataFrame()
    con=duckdb.connect()
    legs=[]
    for rec in setup_rows.itertuples(index=False):
        for leg,strike in (
            ('call',rec.call_strike),('put',rec.put_strike),
            ('call_wing',rec.call_wing_strike),('put_wing',rec.put_wing_strike)
        ):
            legs.append({
                'trade_date':rec.trade_date,'expiry_type':rec.expiry_type,
                'entry_time':rec.entry_time,'leg':leg,'strike':float(strike)
            })
    leg_df=pd.DataFrame(legs).drop_duplicates()
    con.register('legs',leg_df)
    expiry_type = str(setup_rows.expiry_type.iloc[0])
    g=required_files_sql(root, expiry_type=expiry_type)
    q=f'''
    SELECT CAST(o.datetime AS TIMESTAMP) AS datetime,
           o.expiry_type,
           CAST(o.open AS DOUBLE) AS open,
           CAST(o.high AS DOUBLE) AS high,
           CAST(o.low AS DOUBLE) AS low,
           CAST(o.close AS DOUBLE) AS close,
           CAST(o.strike_price AS DOUBLE) AS strike,
           l.trade_date AS trade_date,
           l.entry_time AS entry_time,
           l.leg AS leg
    FROM read_parquet({g}, union_by_name=true) o
    JOIN legs l
      ON o.expiry_type=l.expiry_type
     AND CAST(o.strike_price AS DOUBLE)=l.strike
     AND CAST(o.datetime AS TIMESTAMP)>=l.entry_time
     AND CAST(o.datetime AS TIMESTAMP)<=l.entry_time + INTERVAL '60 minutes'
     AND CAST(CAST(o.datetime AS TIMESTAMP) + INTERVAL '5 hours 30 minutes' AS DATE)=l.trade_date
    WHERE o.close>0
    '''
    out=con.execute(q).df()
    con.close()
    if out.empty:
        return out
    out['datetime']=pd.to_datetime(out['datetime']).dt.floor('min')
    out['entry_time']=pd.to_datetime(out['entry_time']).dt.floor('min')
    out['trade_date']=pd.to_datetime(out['trade_date']).dt.date
    return out

def pick_setup(entry_quotes,signal):
    ts=pd.Timestamp(signal.datetime)+pd.Timedelta(minutes=1)
    e=entry_quotes[
        (entry_quotes.trade_date==signal.trade_date)
        & (entry_quotes.expiry_type==signal.expiry_type)
        & (entry_quotes.datetime==ts)
    ]
    if e.empty:return None
    d={}
    for side in ('CALL','PUT'):
        atm=e[(e.option_type==side)&(e.strike_type=='ATM')]
        wing=e[(e.option_type==side)&(e.strike_type==('ATM+2' if side=='CALL' else 'ATM-2'))]
        if atm.empty or wing.empty:return None
        d[side]=(float(atm.iloc[0].strike),float(atm.iloc[0].open),float(wing.iloc[0].strike),float(wing.iloc[0].open))
    return {
        'entry_time':ts,
        'call_strike':d['CALL'][0],'call_entry':d['CALL'][1],
        'call_wing_strike':d['CALL'][2],'call_wing_entry':d['CALL'][3],
        'put_strike':d['PUT'][0],'put_entry':d['PUT'][1],
        'put_wing_strike':d['PUT'][2],'put_wing_entry':d['PUT'][3],
    }

def bars_from_long_window(window_rows,key,hold):
    if window_rows.empty:
        return pd.DataFrame()
    d,e,et=key
    q=window_rows[
        (window_rows.trade_date==d)
        & (window_rows.expiry_type==e)
        & (window_rows.entry_time==et)
        & (window_rows.datetime<=et+pd.Timedelta(minutes=hold))
    ]
    if q.empty:return pd.DataFrame()
    wide=q.pivot_table(index='datetime',columns='leg',values=['open','high','low','close'],aggfunc='last').reset_index()
    if wide.empty:return pd.DataFrame()
    cols=[]
    for c in wide.columns:
        if isinstance(c,tuple):
            if c[0]=='datetime' or c[1]=='':
                cols.append('datetime')
            else:
                cols.append(f'{c[1]}_{c[0]}')
        else:
            cols.append(str(c))
    wide.columns=cols
    needed=['datetime','call_open','call_high','call_low','call_close','put_open','put_high','put_low','put_close','call_wing_open','call_wing_high','call_wing_low','call_wing_close','put_wing_open','put_wing_high','put_wing_low','put_wing_close']
    missing=[c for c in needed if c not in wide.columns]
    if missing:
        return pd.DataFrame()
    return wide[needed].sort_values('datetime')

def lot_size_for_trade_date(d):
    d=pd.Timestamp(d).date()
    if d < pd.Timestamp('2024-04-26').date(): return 50
    if d < pd.Timestamp('2024-11-21').date(): return 25
    if d < pd.Timestamp('2026-01-06').date(): return 75
    return 65
def simulate(signal,setup,bars,structure,stop_ratio,slippage):
    if bars.empty:return None
    entry_pkg=(setup['call_entry']+setup['put_entry']) if structure=='STRADDLE' else (setup['call_entry']+setup['put_entry']-setup['call_wing_entry']-setup['put_wing_entry'])
    if entry_pkg<=0:return None
    stop=entry_pkg*stop_ratio; target=entry_pkg*TARGET_RATIO; exit_ts=bars.datetime.iloc[-1]; reason='TIME'
    for _,b in bars.iterrows():
        if structure=='STRADDLE': worst=b.call_high+b.put_high; best=b.call_low+b.put_low
        else: worst=b.call_high+b.put_high-b.call_wing_low-b.put_wing_low; best=b.call_low+b.put_low-b.call_wing_high-b.put_wing_high
        if worst>=stop: exit_ts=b.datetime; reason='STOP'; break
        if best<=target: exit_ts=b.datetime; reason='TARGET'; break
    ex=bars[bars.datetime==exit_ts].iloc[-1]; lot=lot_size_for_trade_date(signal.trade_date)
    cm=OptionCostModel()
    if structure=='STRADDLE':
        net=cm.short_straddle_net_pnl(setup['call_entry'],setup['put_entry'],float(ex.call_close),float(ex.put_close),lot_size=lot,slippage_points=slippage)
    else:
        net=cm.four_leg_defined_net_pnl(setup['call_entry'],setup['call_wing_entry'],setup['put_entry'],setup['put_wing_entry'],float(ex.call_close),float(ex.call_wing_close),float(ex.put_close),float(ex.put_wing_close),lot_size=lot,leg_signs=(-1,1,-1,1),slippage_points=slippage)
    return {'trade_date':signal.trade_date,'signal_time':signal.datetime,'entry_time':setup['entry_time'],'exit_time':exit_ts,'expiry_type':signal.expiry_type,'structure':structure,'vrp':float(signal.vrp),'abs_ret15':float(signal.abs_ret15),'reason':reason,'net_pnl':float(net)}

def walk_forward(trades):
    if trades.empty:return pd.DataFrame()
    dates=sorted(pd.to_datetime(trades.trade_date).dt.date.unique()); train_n,val_n,embargo_n,test_n,step_n=90,30,5,30,30; rows=[]; start=0
    while start+train_n+val_n+embargo_n+test_n<=len(dates):
        trd=set(dates[start:start+train_n]); vad=set(dates[start+train_n:start+train_n+val_n]); ted=set(dates[start+train_n+val_n+embargo_n:start+train_n+val_n+embargo_n+test_n]); tr=trades[trades.trade_date.isin(trd)]; va=trades[trades.trade_date.isin(vad)]; te=trades[trades.trade_date.isin(ted)]
        ranked=[]
        for v,g in tr.groupby('variant_id'):
            d=g.groupby('trade_date').net_pnl.sum()
            if len(d)>=10: ranked.append((v,float(d.mean())))
        ranked.sort(key=lambda x:x[1],reverse=True); val=[]
        for v,_ in ranked[:24]:
            g=va[va.variant_id.eq(v)]
            if len(g)>=5: val.append((v,float(g.groupby('trade_date').net_pnl.sum().mean())))
        if not val: start+=step_n; continue
        val.sort(key=lambda x:x[1],reverse=True); sel=val[0][0]; g=te[te.variant_id.eq(sel)]; d=g.groupby('trade_date').net_pnl.sum()
        rows.append({'test_start':str(min(ted)),'test_end':str(max(ted)),'selected_variant':sel,'validation_mean':val[0][1],'test_mean':float(d.mean()),'positive_day_rate':float((d>0).mean()),'trade_days':int(len(d))}); start+=step_n
    return pd.DataFrame(rows)

def run(data_root,out,slippage,expiry_type=None):
    features=load_signal_rows(data_root, expiry_type=expiry_type)
    variants=[v for v in variant_grid() if (expiry_type is None or v['expiry_type']==expiry_type)]
    unique_signals=features[['trade_date','datetime','expiry_type','spot','vrp','abs_ret15']].drop_duplicates(['trade_date','datetime','expiry_type'])
    entry_quotes=load_entry_quotes(data_root,unique_signals)
    entry_groups={key:g.copy() for key,g in entry_quotes.groupby(['trade_date','expiry_type','datetime'],sort=False)}

    setup_cache={}
    setup_rows=[]
    for signal in unique_signals.itertuples(index=False):
        key=(signal.trade_date,signal.expiry_type,pd.Timestamp(signal.datetime)+pd.Timedelta(minutes=1))
        g=entry_groups.get(key)
        if g is None:
            continue
        setup=pick_setup(g,signal)
        if setup is None:
            continue
        setup_cache[(signal.trade_date,signal.datetime,signal.expiry_type)]=setup
        setup_rows.append({
            'trade_date':signal.trade_date,
            'expiry_type':signal.expiry_type,
            'entry_time':setup['entry_time'],
            'call_strike':setup['call_strike'],
            'put_strike':setup['put_strike'],
            'call_wing_strike':setup['call_wing_strike'],
            'put_wing_strike':setup['put_wing_strike'],
        })

    setup_df=pd.DataFrame(setup_rows).drop_duplicates()
    window_rows=load_execution_windows(data_root,setup_df,max_hold=max(HOLDS))
    window_cache={}
    if not window_rows.empty:
        for key in window_rows[['trade_date','expiry_type','entry_time']].drop_duplicates().itertuples(index=False,name=None):
            window_cache[key]=window_rows[(window_rows.trade_date==key[0])&(window_rows.expiry_type==key[1])&(window_rows.entry_time==key[2])].copy()

    trades=[]
    for v in variants:
        sig=select_signals(features,v)
        if sig.empty: continue
        for _,signal in sig.iterrows():
            key=(signal.trade_date,signal.datetime,signal.expiry_type)
            setup=setup_cache.get(key)
            if setup is None: continue
            wkey=(signal.trade_date,signal.expiry_type,setup['entry_time'])
            bars=bars_from_long_window(window_cache.get(wkey,pd.DataFrame()),wkey,v['hold_minutes'])
            t=simulate(signal,setup,bars,v['structure'],v['stop_ratio'],slippage)
            if t is not None:
                t['variant_id']=f"{v['entry_time']}|vrp{v['vrp_threshold']:.1f}|jump{v['jump_max']:.4f}|{v['structure']}|{v['expiry_type']}|h{v['hold_minutes']}|s{v['stop_ratio']:.2f}"
                trades.append(t)

    trades=pd.DataFrame(trades)
    out.mkdir(parents=True,exist_ok=True)
    if not trades.empty: trades.to_csv(out/'phase15_trades.csv',index=False)
    rows=[]
    if not trades.empty:
        total_days=features.trade_date.nunique()
        for vid,g in trades.groupby('variant_id'):
            d=g.groupby('trade_date').net_pnl.sum()
            wins=g.loc[g.net_pnl>0,'net_pnl'].sum()
            losses=-g.loc[g.net_pnl<0,'net_pnl'].sum()
            rows.append({
                'variant_id':vid,'trades':len(g),'active_days':len(d),
                'mean_active_day_net':float(d.mean()),
                'mean_all_day_net':float(d.sum()/max(1,total_days)),
                'win_rate':float((g.net_pnl>0).mean()),
                'profit_factor':float(wins/max(1e-9,losses)),
                'max_drawdown':float((d.cumsum()-d.cumsum().cummax()).min()),
                'total_net':float(g.net_pnl.sum())
            })
    board=pd.DataFrame(rows).sort_values('mean_all_day_net',ascending=False) if rows else pd.DataFrame()
    board.to_csv(out/'phase15_leaderboard.csv',index=False)
    wf=walk_forward(trades)
    wf.to_csv(out/'phase15_walk_forward.csv',index=False)
    result={
        'variants':len(variants),
        'expiry_shard':expiry_type,
        'entry_quote_rows':int(len(entry_quotes)),
        'entry_group_count':int(len(entry_groups)),
        'feature_rows':int(len(features)),
        'unique_candidate_signals':int(len(unique_signals)),
        'setup_count':int(len(setup_cache)),
        'window_rows':int(len(window_rows)),
        'trade_rows':int(len(trades)),
        'positive_variants':int((board.mean_all_day_net>0).sum()) if not board.empty else 0,
        'target_qualified_prelim':int((board.mean_all_day_net>=TARGET).sum()) if not board.empty else 0,
        'best':board.iloc[0].to_dict() if not board.empty else None,
        'walk_forward_windows':int(len(wf)),
        'positive_test_windows':int((wf.test_mean>0).sum()) if not wf.empty else 0,
        'target_test_windows':int((wf.test_mean>=TARGET).sum()) if not wf.empty else 0,
        'mean_test_window_net':float(wf.test_mean.mean()) if not wf.empty else None,
        'slippage_points_per_leg':slippage,
        'gate':'PASS_PRELIMINARY' if (not board.empty and board.iloc[0].mean_all_day_net>=TARGET and not wf.empty and (wf.test_mean>=TARGET).any()) else 'FAIL_PRELIMINARY'
    }
    (out/'phase15_summary.json').write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,indent=2,default=str))
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--data',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--slippage',type=float,default=0.20); ap.add_argument('--expiry-type',choices=['WEEK','MONTH']); a=ap.parse_args(); run(a.data,a.out,a.slippage,a.expiry_type)