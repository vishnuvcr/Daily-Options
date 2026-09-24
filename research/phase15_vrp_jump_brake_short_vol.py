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

def parquet_glob(root:Path)->str: return (root/'**'/'*.parquet').as_posix()

def feature_query(root:Path)->str:
    g=parquet_glob(root); times=','.join(repr(x) for x in ENTRY_TIMES)
    return f'''
    WITH base AS (
      SELECT CAST(datetime AS TIMESTAMP) AS datetime, CAST(date AS DATE) AS trade_date, expiry_type, option_type, strike_type, CAST(spot AS DOUBLE) AS spot, CAST(iv AS DOUBLE) AS iv, CAST(close AS DOUBLE) AS close
      FROM read_parquet('{g}', union_by_name=true)
      WHERE close>0 AND option_type IN ('CALL','PUT') AND expiry_type IN ('WEEK','MONTH')
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

def load_signal_rows(root):
    con=duckdb.connect(); out=con.execute(feature_query(root)).df(); con.close()
    if out.empty: return out
    out.trade_date=pd.to_datetime(out.trade_date).dt.date; out.datetime=pd.to_datetime(out.datetime)
    return out

def select_signals(features,variant):
    m=features.datetime.dt.strftime('%H:%M:%S').eq(variant['entry_time']) & features.vrp.ge(variant['vrp_threshold']) & features.abs_ret15.le(variant['jump_max']) & features.expiry_type.eq(variant['expiry_type'])
    x=features[m].copy()
    return x.sort_values(['trade_date','datetime']).drop_duplicates(['trade_date','expiry_type'])[['trade_date','datetime','expiry_type','spot','vrp','abs_ret15']]
def load_entry_quotes(root,signals):
    if signals.empty:return pd.DataFrame()
    con=duckdb.connect(); con.register('setups',signals[['trade_date','expiry_type']].drop_duplicates())
    g=parquet_glob(root)
    q=f'''
    SELECT CAST(o.datetime AS TIMESTAMP) AS datetime, CAST(o.date AS DATE) AS trade_date, o.expiry_type, o.option_type, o.strike_type, CAST(o.strike_price AS DOUBLE) AS strike, CAST(o.open AS DOUBLE) AS open, CAST(o.high AS DOUBLE) AS high, CAST(o.low AS DOUBLE) AS low, CAST(o.close AS DOUBLE) AS close
    FROM read_parquet('{g}', union_by_name=true) o JOIN setups s ON CAST(o.date AS DATE)=s.trade_date AND o.expiry_type=s.expiry_type
    WHERE o.close>0 AND o.option_type IN ('CALL','PUT')
    '''
    out=con.execute(q).df(); con.close(); return out
def pick_setup(entry_quotes,signal):
    ts=pd.Timestamp(signal.datetime)+pd.Timedelta(minutes=1)
    e=entry_quotes[(entry_quotes.trade_date==signal.trade_date)&(entry_quotes.expiry_type==signal.expiry_type)&(entry_quotes.expiry==signal.expiry)&(entry_quotes.datetime==ts)]
    if e.empty: return None
    d={}
    for side in ('CALL','PUT'):
        atm=e[(e.option_type==side)&(e.strike_type=='ATM')]; wing=e[(e.option_type==side)&(e.strike_type==('ATM+2' if side=='CALL' else 'ATM-2'))]
        if atm.empty or wing.empty: return None
        d[side]=(float(atm.iloc[0].strike),float(atm.iloc[0].open),float(wing.iloc[0].strike),float(wing.iloc[0].open))
    return {'entry_time':ts,'call_strike':d['CALL'][0],'call_entry':d['CALL'][1],'call_wing_strike':d['CALL'][2],'call_wing_entry':d['CALL'][3],
            'put_strike':d['PUT'][0],'put_entry':d['PUT'][1],'put_wing_strike':d['PUT'][2],'put_wing_entry':d['PUT'][3]}

def build_window(entry_quotes,signal,setup,hold):
    end=setup['entry_time']+pd.Timedelta(minutes=hold)
    q=entry_quotes[(entry_quotes.trade_date==signal.trade_date)&(entry_quotes.expiry_type==signal.expiry_type)&(entry_quotes.expiry==signal.expiry)&(entry_quotes.datetime>=setup['entry_time'])&(entry_quotes.datetime<=end)]
    frames=[]
    for name,strike,side in [('call',setup['call_strike'],'CALL'),('put',setup['put_strike'],'PUT'),('call_wing',setup['call_wing_strike'],'CALL'),('put_wing',setup['put_wing_strike'],'PUT')]:
        x=q[(q.option_type==side)&(q.strike==strike)][['datetime','open','high','low','close']].copy()
        if x.empty: return pd.DataFrame()
        x=x.rename(columns={c:f'{name}_{c}' for c in ['open','high','low','close']}); frames.append(x)
    out=frames[0]
    for x in frames[1:]: out=out.merge(x,on='datetime',how='inner')
    return out.sort_values('datetime')

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
    return {'trade_date':signal.trade_date,'signal_time':signal.datetime,'entry_time':setup['entry_time'],'exit_time':exit_ts,'expiry_type':signal.expiry_type,'expiry':signal.expiry,'structure':structure,'vrp':float(signal.vrp),'abs_ret15':float(signal.abs_ret15),'reason':reason,'net_pnl':float(net)}

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

def run(data_root,out,slippage):
    features=load_signal_rows(data_root); variants=variant_grid()
    all_candidate_signals=features[['trade_date','datetime','expiry_type','spot','vrp','abs_ret15']].drop_duplicates(['trade_date','datetime','expiry_type'])
    eq=load_entry_quotes(data_root,all_candidate_signals)
    setup_cache={}
    for _,sig in all_candidate_signals.iterrows():
        setup=pick_setup(eq,sig)
        if setup is not None: setup_cache[(sig.trade_date,sig.datetime,sig.expiry_type)]=setup
    window_cache={}
    trades=[]
    for v in variants:
        sig=select_signals(features,v)
        if sig.empty: continue
        for _,signal in sig.iterrows():
            key=(signal.trade_date,signal.datetime,signal.expiry_type)
            setup=setup_cache.get(key)
            if setup is None: continue
            wkey=(key,v['hold_minutes'])
            if wkey not in window_cache: window_cache[wkey]=build_window(eq,signal,setup,v['hold_minutes'])
            bars=window_cache[wkey]
            t=simulate(signal,setup,bars,v['structure'],v['stop_ratio'],slippage)
            if t is not None:
                t['variant_id']=f"{v['entry_time']}|vrp{v['vrp_threshold']:.1f}|jump{v['jump_max']:.4f}|{v['structure']}|{v['expiry_type']}|h{v['hold_minutes']}|s{v['stop_ratio']:.2f}"; trades.append(t)
    trades=pd.DataFrame(trades); out.mkdir(parents=True,exist_ok=True)
    if not trades.empty: trades.to_csv(out/'phase15_trades.csv',index=False)
    rows=[]
    if not trades.empty:
        total_days=features.trade_date.nunique()
        for vid,g in trades.groupby('variant_id'):
            d=g.groupby('trade_date').net_pnl.sum(); wins=g.loc[g.net_pnl>0,'net_pnl'].sum(); losses=-g.loc[g.net_pnl<0,'net_pnl'].sum()
            rows.append({'variant_id':vid,'trades':len(g),'active_days':len(d),'mean_active_day_net':float(d.mean()),'mean_all_day_net':float(d.sum()/max(1,total_days)),'win_rate':float((g.net_pnl>0).mean()),'profit_factor':float(wins/max(1e-9,losses)),'max_drawdown':float((d.cumsum()-d.cumsum().cummax()).min()),'total_net':float(g.net_pnl.sum())})
    board=pd.DataFrame(rows).sort_values('mean_all_day_net',ascending=False) if rows else pd.DataFrame(); board.to_csv(out/'phase15_leaderboard.csv',index=False); wf=walk_forward(trades); wf.to_csv(out/'phase15_walk_forward.csv',index=False)
    result={'variants':VARIANT_COUNT,'feature_rows':int(len(features)),'unique_candidate_signals':int(len(all_candidate_signals)),'setup_count':int(len(setup_cache)),'trade_rows':int(len(trades)),'positive_variants':int((board.mean_all_day_net>0).sum()) if not board.empty else 0,'target_qualified_prelim':int((board.mean_all_day_net>=TARGET).sum()) if not board.empty else 0,'best':board.iloc[0].to_dict() if not board.empty else None,'walk_forward_windows':int(len(wf)),'positive_test_windows':int((wf.test_mean>0).sum()) if not wf.empty else 0,'target_test_windows':int((wf.test_mean>=TARGET).sum()) if not wf.empty else 0,'mean_test_window_net':float(wf.test_mean.mean()) if not wf.empty else None,'slippage_points_per_leg':slippage,'gate':'PASS_PRELIMINARY' if (not board.empty and board.iloc[0].mean_all_day_net>=TARGET and not wf.empty and (wf.test_mean>=TARGET).any()) else 'FAIL_PRELIMINARY'}
    (out/'phase15_summary.json').write_text(json.dumps(result,indent=2,default=str)); print(json.dumps(result,indent=2,default=str)); return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--data',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--slippage',type=float,default=0.20); a=ap.parse_args(); run(a.data,a.out,a.slippage)