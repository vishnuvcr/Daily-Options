from __future__ import annotations

import argparse, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from research.cost_model import OptionCostModel
from research.phase14_global_cross_market_opening_gap import load_global_data, build_features

FROZEN_GLOBAL_Z=0.5; FROZEN_GAP_THRESHOLD=0.0075; FROZEN_SIGNAL_TIME='09:30:00'; FROZEN_HOLD=20
FROZEN_RISK={'stop_pct':0.30,'target_pct':0.60}; VALIDATION_START=pd.Timestamp('2021-08-01').date(); VALIDATION_END=pd.Timestamp('2024-03-31').date(); LOT_SIZE=50

def parquet_glob(root): return (root/'NIFTY'/'MONTH'/'**'/'*.parquet').as_posix()

def load_later_spot(root):
    con=duckdb.connect(); g=parquet_glob(root)
    q=f"SELECT CAST(datetime AS TIMESTAMP) datetime, MAX(CAST(spot AS DOUBLE)) spot_close FROM read_parquet('{g}', union_by_name=true) WHERE date BETWEEN DATE '2021-08-01' AND DATE '2024-03-31' AND spot>0 GROUP BY 1 ORDER BY 1"
    x=con.execute(q).df(); con.close()
    if x.empty: raise RuntimeError('No later-period spot data found')
    return x

def frozen_signal_dates(features):
    x=features[(features.trade_time_ist==FROZEN_SIGNAL_TIME)&(features.global_global3.abs()>=FROZEN_GLOBAL_Z)&(features.gap_signal.abs()>=FROZEN_GAP_THRESHOLD)].copy()
    x=x[np.sign(x.global_global3)!=np.sign(x.gap_signal)].copy()
    rows=[]
    for d,day in x.groupby('trade_date',sort=True):
        r=day.iloc[0]
        rows.append({'trade_date':d,'signal_time':r.datetime,'entry_time':r.datetime+pd.Timedelta(minutes=1),'direction':'CALL' if float(r.gap_signal)<0 else 'PUT','spot':float(r.spot_close),'global3':float(r.global_global3),'gap':float(r.gap_signal)})
    return pd.DataFrame(rows)

def load_month_option_rows(root, signal_days):
    if signal_days.empty: return pd.DataFrame()
    g=parquet_glob(root); start=min(signal_days.trade_date); end=max(signal_days.trade_date)
    con=duckdb.connect()
    q=f"SELECT CAST(datetime AS TIMESTAMP) datetime, CAST(date AS DATE) trade_date, CAST(open AS DOUBLE) open, CAST(high AS DOUBLE) high, CAST(low AS DOUBLE) low, CAST(close AS DOUBLE) AS close_px, CAST(strike_price AS DOUBLE) strike_price, CAST(option_type AS VARCHAR) option_type, CAST(strike_type AS VARCHAR) strike_type FROM read_parquet('{g}', union_by_name=true) WHERE date BETWEEN DATE '{start}' AND DATE '{end}' AND expiry_type='MONTH' AND close>0 AND option_type IN ('CALL','PUT')"
    x=con.execute(q).df(); con.close(); return x

def simulate(signals, options, slippage):
    if signals.empty or options.empty: return pd.DataFrame()
    cm=OptionCostModel(); rows=[]
    for rec in signals.itertuples(index=False):
        day_opts=options[(options.trade_date==rec.trade_date)&(options.option_type==rec.direction)].copy()
        if day_opts.empty: continue
        at_signal=day_opts[(day_opts.datetime==pd.Timestamp(rec.signal_time))&(day_opts.strike_type=='ATM')]
        if at_signal.empty: continue
        strike=float(at_signal.sort_values('strike_price').iloc[0].strike_price)
        entry=pd.Timestamp(rec.entry_time); end=entry+pd.Timedelta(minutes=FROZEN_HOLD)
        bars=day_opts[(day_opts.strike_price==strike)&(day_opts.datetime>=entry)&(day_opts.datetime<=end)].sort_values('datetime')
        if bars.empty or bars.iloc[0].datetime>entry: continue
        first=bars.iloc[0]; entry_px=float(first.open)
        if not np.isfinite(entry_px) or entry_px<=0: continue
        stop=entry_px*(1-FROZEN_RISK['stop_pct']); target=entry_px*(1+FROZEN_RISK['target_pct']); exit_ts=bars.iloc[-1].datetime; reason='TIME'
        for _,b in bars.iterrows():
            if float(b.low)<=stop: exit_ts=b.datetime; reason='STOP'; break
            if float(b.high)>=target: exit_ts=b.datetime; reason='TARGET'; break
        ex=bars[bars.datetime==exit_ts].iloc[-1]; net=cm.net_pnl(entry_px,float(ex.close),qty=1,lot_size=LOT_SIZE,slippage_points=slippage)
        rows.append({'trade_date':rec.trade_date,'year':pd.Timestamp(rec.trade_date).year,'direction':rec.direction,'signal_time':rec.signal_time,'entry_time':rec.entry_time,'exit_time':exit_ts,'reason':reason,'strike':strike,'entry_premium':entry_px,'exit_premium':float(ex.close),'global3':rec.global3,'gap':rec.gap,'net_pnl':net})
    return pd.DataFrame(rows)

def summarize(trades,slippage):
    if trades.empty: return {'frozen_rule':True,'trades':0,'gate':'NO_TRADES','slippage_points_per_leg':slippage}
    daily=trades.groupby('trade_date').net_pnl.sum(); years=[]
    for year,g in trades.groupby('year'):
        yd=g.groupby('trade_date').net_pnl.sum(); years.append({'year':int(year),'trades':int(len(g)),'active_days':int(len(yd)),'mean_active_day_net':float(yd.mean()),'median_active_day_net':float(yd.median()),'win_rate':float((g.net_pnl>0).mean()),'total_net':float(g.net_pnl.sum())})
    mean_active=float(daily.mean()); positive_years=sum(y['mean_active_day_net']>0 for y in years); gate='PASS_CANDIDATE' if mean_active>=1000 and positive_years>=2 and len(trades)>=100 else 'FAIL_LATER_OOS'
    return {'frozen_rule':True,'global_z':FROZEN_GLOBAL_Z,'gap_threshold':FROZEN_GAP_THRESHOLD,'mode':'FADE','signal_time':FROZEN_SIGNAL_TIME,'structure':'LONG','expiry_mode':'MONTH','hold':FROZEN_HOLD,'risk':FROZEN_RISK,'validation_start':str(VALIDATION_START),'validation_end':str(VALIDATION_END),'lot_size':LOT_SIZE,'trades':int(len(trades)),'active_days':int(len(daily)),'mean_active_day_net':mean_active,'median_active_day_net':float(daily.median()),'mean_calendar_day_net':float(daily.sum()/max(1,(VALIDATION_END-VALIDATION_START).days+1)),'win_rate':float((trades.net_pnl>0).mean()),'profit_factor':float(trades.loc[trades.net_pnl>0,'net_pnl'].sum()/max(1e-9,-trades.loc[trades.net_pnl<0,'net_pnl'].sum())),'max_drawdown':float((daily.cumsum()-daily.cumsum().cummax()).min()),'target_mean':bool(mean_active>=1000),'positive_years':int(positive_years),'years':years,'gate':gate,'slippage_points_per_leg':slippage}

def run(root,global_root,out,slippage):
    spot=load_later_spot(root)
    gd=load_global_data(global_root)
    features=build_features(spot,gd)
    features=features[(features.trade_date>=VALIDATION_START)&(features.trade_date<=VALIDATION_END)].copy()
    signals=frozen_signal_dates(features)
    options=load_month_option_rows(root,signals)

    option_dates = set(options.trade_date.dropna().tolist()) if not options.empty else set()
    signal_dates = set(signals.trade_date.dropna().tolist()) if not signals.empty else set()
    diagnostic = {
        "spot_rows": int(len(spot)),
        "feature_rows": int(len(features)),
        "frozen_signal_days": int(len(signals)),
        "signal_dates": sorted(str(x) for x in signal_dates),
        "option_rows_loaded": int(len(options)),
        "option_date_min": str(options.trade_date.min()) if not options.empty else None,
        "option_date_max": str(options.trade_date.max()) if not options.empty else None,
        "signal_option_date_overlap": int(len(signal_dates.intersection(option_dates))),
        "option_type_values": sorted(str(x) for x in options.option_type.dropna().unique()) if not options.empty else [],
        "signal_days_with_any_option_rows": 0,
        "signal_days_with_direction_rows": 0,
        "signal_days_with_atm_at_signal_timestamp": 0,
        "signal_days_with_post_entry_atm_bars": 0,
    }

    if not signals.empty and not options.empty:
        for rec in signals.itertuples(index=False):
            any_day_opts = options[options.trade_date == rec.trade_date]
            if not any_day_opts.empty:
                diagnostic["signal_days_with_any_option_rows"] += 1
            day_opts = any_day_opts[any_day_opts.option_type == rec.direction]
            if day_opts.empty:
                continue
            diagnostic["signal_days_with_direction_rows"] += 1
            at_signal = day_opts[(day_opts.datetime == pd.Timestamp(rec.signal_time)) & (day_opts.strike_type == "ATM")]
            if at_signal.empty:
                continue
            diagnostic["signal_days_with_atm_at_signal_timestamp"] += 1
            strike = float(at_signal.sort_values("strike_price").iloc[0].strike_price)
            entry = pd.Timestamp(rec.entry_time)
            post = day_opts[(day_opts.strike_price == strike) & (day_opts.datetime >= entry) & (day_opts.datetime <= entry + pd.Timedelta(minutes=FROZEN_HOLD))]
            if not post.empty:
                diagnostic["signal_days_with_post_entry_atm_bars"] += 1

    trades=simulate(signals,options,slippage)
    out.mkdir(parents=True,exist_ok=True)
    trades.to_csv(out/'phase14_later_oos_trades.csv',index=False)
    s=summarize(trades,slippage)
    s["diagnostic"]=diagnostic
    (out/'phase14_later_oos_summary.json').write_text(json.dumps(s,indent=2,default=str))
    print(json.dumps(s,indent=2,default=str))
    return s

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--global-root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--slippage',type=float,default=0.20); a=ap.parse_args(); run(a.root,a.global_root,a.out,a.slippage)