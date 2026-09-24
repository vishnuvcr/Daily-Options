from __future__ import annotations

import argparse, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from research.cost_model import OptionCostModel
from research.phase10_contracts import index_option_lot_size
from research.phase14_global_cross_market_opening_gap import load_global_data, build_features

FROZEN_GLOBAL_Z=0.5; FROZEN_GAP_THRESHOLD=0.0075; FROZEN_SIGNAL_TIME='09:30:00'; FROZEN_HOLD=20
FROZEN_RISK={'stop_pct':0.30,'target_pct':0.60}
VALIDATION_START=pd.Timestamp('2024-10-01').date(); VALIDATION_END=pd.Timestamp('2026-06-30').date()

def load_index(root):
    df=pd.read_parquet(root/'index'/'NIFTY.parquet')
    ts=pd.to_datetime(df['timestamp'],utc=True)
    return pd.DataFrame({'datetime':ts.dt.tz_convert('UTC').dt.tz_localize(None),'spot_close':pd.to_numeric(df['close'],errors='coerce')}).dropna().sort_values('datetime')

def frozen_signal_dates(features):
    x=features[(features.trade_time_ist==FROZEN_SIGNAL_TIME)&(features.global_global3.abs()>=FROZEN_GLOBAL_Z)&(features.gap_signal.abs()>=FROZEN_GAP_THRESHOLD)].copy()
    x=x[np.sign(x.global_global3)!=np.sign(x.gap_signal)].copy()
    rows=[]
    for d,day in x.groupby('trade_date',sort=True):
        r=day.iloc[0]
        rows.append({'trade_date':d,'signal_time':r.datetime,'entry_time':r.datetime+pd.Timedelta(minutes=1),'direction':'CALL' if float(r.gap_signal)<0 else 'PUT','spot':float(r.spot_close),'global3':float(r.global_global3),'gap':float(r.gap_signal)})
    return pd.DataFrame(rows)

def load_options(root,signals):
    if signals.empty: return pd.DataFrame()
    dates=sorted({str(x) for x in signals.trade_date}); start=min(dates); end=max(dates)
    glob=(root/'upstox_intraday'/'NIFTY'/'NIFTY_*.parquet').as_posix()
    con=duckdb.connect()
    q=f"SELECT CAST(timestamp AS TIMESTAMPTZ) AT TIME ZONE 'UTC' AS datetime_utc, CAST(date AS DATE) AS trade_date, CAST(expiry AS DATE) AS expiry, CAST(strike AS DOUBLE) AS strike, CAST(option_type AS VARCHAR) AS option_type, CAST(open AS DOUBLE) AS open, CAST(high AS DOUBLE) AS high, CAST(low AS DOUBLE) AS low, CAST(close AS DOUBLE) AS close FROM read_parquet('{glob}',union_by_name=true) WHERE CAST(date AS DATE) BETWEEN DATE '2024-10-01' AND DATE '2026-06-30' AND underlying='NIFTY' AND granularity='1min' AND expiry IS NOT NULL AND close>0"
    x=con.execute(q).df(); con.close()
    if x.empty: return x
    x['trade_date']=pd.to_datetime(x['trade_date'],errors='coerce').dt.date
    x['expiry']=pd.to_datetime(x['expiry'],errors='coerce').dt.date
    x['option_type']=x['option_type'].replace({'CE':'CALL','PE':'PUT'})
    x['datetime_utc']=pd.to_datetime(x['datetime_utc'],utc=True).dt.tz_localize(None)
    return x

def monthly_expiry_calendar(options):
    if options.empty: return []
    e=pd.DataFrame({'expiry':sorted(set(options.expiry.dropna()))})
    e['ym']=pd.to_datetime(e.expiry).dt.to_period('M')
    monthly=e.groupby('ym',as_index=False).expiry.max()
    return sorted(pd.to_datetime(monthly.expiry).dt.date.tolist())

def simulate(signals,options,slippage):
    if signals.empty or options.empty: return pd.DataFrame()
    monthlies=monthly_expiry_calendar(options); cm=OptionCostModel(); rows=[]
    for rec in signals.itertuples(index=False):
        expiry_candidates=[d for d in monthlies if d>rec.trade_date]
        if not expiry_candidates: continue
        expiry=expiry_candidates[0]
        day=options[(options.trade_date==rec.trade_date)&(options.expiry==expiry)&(options.option_type==rec.direction)].copy()
        if day.empty: continue
        at_signal=day[day.datetime_utc==pd.Timestamp(rec.signal_time)]
        if at_signal.empty: continue
        atm=float(at_signal.iloc[(at_signal['strike']-float(rec.spot)).abs().argsort().iloc[0]].strike)
        entry=pd.Timestamp(rec.entry_time); end=entry+pd.Timedelta(minutes=FROZEN_HOLD)
        bars=day[(day.strike==atm)&(day.datetime_utc>=entry)&(day.datetime_utc<=end)].sort_values('datetime_utc')
        if bars.empty or bars.iloc[0].datetime_utc>entry: continue
        first=bars.iloc[0]; entry_px=float(first.open)
        if not np.isfinite(entry_px) or entry_px<=0: continue
        stop=entry_px*(1-FROZEN_RISK['stop_pct']); target=entry_px*(1+FROZEN_RISK['target_pct']); exit_ts=bars.iloc[-1].datetime_utc; reason='TIME'
        for _,bar in bars.iterrows():
            if float(bar.low)<=stop: exit_ts=bar.datetime_utc; reason='STOP'; break
            if float(bar.high)>=target: exit_ts=bar.datetime_utc; reason='TARGET'; break
        ex=bars[bars.datetime_utc==exit_ts].iloc[-1]; exit_px=float(ex.close)
        net=cm.net_pnl(entry_px,exit_px,qty=1,lot_size=index_option_lot_size('NIFTY',expiry),slippage_points=slippage)
        rows.append({'trade_date':rec.trade_date,'year':pd.Timestamp(rec.trade_date).year,'direction':rec.direction,'expiry':expiry,'signal_time':rec.signal_time,'entry_time':rec.entry_time,'exit_time':exit_ts,'reason':reason,'strike':atm,'entry_premium':entry_px,'exit_premium':exit_px,'global3':rec.global3,'gap':rec.gap,'net_pnl':net})
    return pd.DataFrame(rows)

def summarize(trades,slippage):
    if trades.empty: return {'frozen_rule':True,'trades':0,'gate':'NO_TRADES','slippage_points_per_leg':slippage}
    daily=trades.groupby('trade_date').net_pnl.sum(); years=[]
    for year,g in trades.groupby('year'):
        yd=g.groupby('trade_date').net_pnl.sum(); years.append({'year':int(year),'trades':int(len(g)),'active_days':int(len(yd)),'mean_active_day_net':float(yd.mean()),'median_active_day_net':float(yd.median()),'win_rate':float((g.net_pnl>0).mean()),'total_net':float(g.net_pnl.sum())})
    mean_active=float(daily.mean()); positive_years=int(sum(y['mean_active_day_net']>0 for y in years)); gate='PASS_CANDIDATE' if mean_active>=1000 and positive_years>=2 and len(trades)>=100 else 'FAIL_LATER_OOS'
    return {'frozen_rule':True,'validation_start':str(VALIDATION_START),'validation_end':str(VALIDATION_END),'trades':int(len(trades)),'active_days':int(len(daily)),'mean_active_day_net':mean_active,'median_active_day_net':float(daily.median()),'mean_calendar_day_net':float(daily.sum()/max(1,(VALIDATION_END-VALIDATION_START).days+1)),'win_rate':float((trades.net_pnl>0).mean()),'profit_factor':float(trades.loc[trades.net_pnl>0,'net_pnl'].sum()/max(1e-9,-trades.loc[trades.net_pnl<0,'net_pnl'].sum())),'max_drawdown':float((daily.cumsum()-daily.cumsum().cummax()).min()),'target_mean':bool(mean_active>=1000),'positive_years':positive_years,'years':years,'gate':gate,'slippage_points_per_leg':slippage}

def run(option_root,index_root,global_root,out,slippage):
    spot=load_index(index_root); gd=load_global_data(global_root); features=build_features(spot,gd); features=features[(features.trade_date>=VALIDATION_START)&(features.trade_date<=VALIDATION_END)].copy(); signals=frozen_signal_dates(features); options=load_options(option_root,signals); trades=simulate(signals,options,slippage); out.mkdir(parents=True,exist_ok=True); trades.to_csv(out/'phase14_rissin_trades.csv',index=False); s=summarize(trades,slippage); s.update({'signal_days':int(len(signals)),'option_rows_loaded':int(len(options)),'monthly_expiry_count':int(len(monthly_expiry_calendar(options)))}); (out/'phase14_rissin_summary.json').write_text(json.dumps(s,indent=2,default=str)); print(json.dumps(s,indent=2,default=str)); return s

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--option-root',type=Path,required=True); ap.add_argument('--index-root',type=Path,required=True); ap.add_argument('--global-root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--slippage',type=float,default=0.20); a=ap.parse_args(); run(a.option_root,a.index_root,a.global_root,a.out,a.slippage)