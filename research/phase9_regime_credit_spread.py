from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel

ENTRY_TIMES = ('09:45:00', '10:15:00')
EXPIRIES = ('WEEK', 'MONTH')
WIDTHS = (2, 3)
HOLDS = (60, 120, 180)
EXIT_PROFILES = (
    {'stop_mult': 1.5, 'target_capture': 0.50},
    {'stop_mult': 2.0, 'target_capture': 0.65},
)
SHORT_OFFSET_STEPS = 3
IV_RV_MIN = 1.10


def open_db() -> duckdb.DuckDBPyConnection:
    Path('/tmp/phase9_duckdb').mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("PRAGMA threads=2")
    con.execute("PRAGMA memory_limit='3GB'")
    con.execute("PRAGMA preserve_insertion_order=false")
    con.execute("PRAGMA temp_directory='/tmp/phase9_duckdb'")
    return con

@dataclass(frozen=True)
class Variant:
    family: str
    entry_time: str
    expiry_type: str
    width_steps: int
    hold_minutes: int
    exit_id: int

    @property
    def key(self) -> str:
        return f'{self.family}|{self.entry_time}|{self.expiry_type}|w{self.width_steps}|h{self.hold_minutes}|x{self.exit_id}'

def variant_grid() -> list[Variant]:
    return [
        Variant(family, entry, expiry, width, hold, exit_id)
        for family in ('BULL_PUT', 'BEAR_CALL')
        for entry in ENTRY_TIMES
        for expiry in EXPIRIES
        for width in WIDTHS
        for hold in HOLDS
        for exit_id in range(len(EXIT_PROFILES))
    ]

def parquet_glob(root: Path) -> str:
    return (root / '**' / '*.parquet').as_posix()

def load_regime_series(root: Path) -> pd.DataFrame:
    glob = parquet_glob(root)
    sql = f'''
    WITH raw AS (
      SELECT CAST(datetime AS TIMESTAMPTZ) AS ts_utc, CAST(date AS DATE) AS trade_date,
             CAST(spot AS DOUBLE) AS spot, CAST(iv AS DOUBLE) AS iv, strike_type, option_type
      FROM read_parquet('{glob}', union_by_name=true)
      WHERE close > 0 AND expiry_type IN ('WEEK','MONTH')
        AND strike_type='ATM' AND option_type IN ('CALL','PUT') AND iv BETWEEN 0 AND 300
    ),
    minute AS (
      SELECT ts_utc, trade_date, MAX(spot) AS spot, AVG(iv) AS atm_iv
      FROM raw GROUP BY ALL
    )
    SELECT * FROM minute ORDER BY trade_date, ts_utc
    '''
    con = duckdb.connect()
    df = con.execute(sql).df()
    con.close()
    if df.empty:
        return df
    df['datetime'] = pd.to_datetime(df['ts_utc'], utc=True) + pd.Timedelta(hours=5, minutes=30)
    df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date
    df = df.sort_values(['trade_date','datetime']).reset_index(drop=True)
    g = df.groupby('trade_date', sort=False)
    log_ret = g['spot'].transform(lambda s: np.log(s / s.shift(1)))
    df['ret5'] = g['spot'].transform(lambda s: s / s.shift(5) - 1.0)
    df['rv20'] = log_ret.groupby(df['trade_date']).transform(lambda s: s.rolling(20, min_periods=20).std()) * np.sqrt(252*375) * 100.0
    df['ema20'] = g['spot'].transform(lambda s: s.ewm(span=20, adjust=False, min_periods=20).mean())
    df['ema50'] = g['spot'].transform(lambda s: s.ewm(span=50, adjust=False, min_periods=50).mean())
    df['iv_rv'] = df['atm_iv'] / df['rv20'].replace(0, np.nan)
    local = df['datetime'].dt.strftime('%H:%M:%S')
    df = df.loc[local.between('09:30:00','12:00:00')].copy()
    df['bull_regime'] = (df['ema20'] > df['ema50']) & (df['ret5'] > 0) & (df['iv_rv'] >= IV_RV_MIN)
    df['bear_regime'] = (df['ema20'] < df['ema50']) & (df['ret5'] < 0) & (df['iv_rv'] >= IV_RV_MIN)
    return df

def variant_keys_for_shard(shard_index: int, shard_count: int) -> set[str]:
    if shard_count < 1 or shard_index < 0 or shard_index >= shard_count:
        raise ValueError('invalid shard index/count')
    return {v.key for i, v in enumerate(variant_grid()) if i % shard_count == shard_index}

def build_signals(regime: pd.DataFrame, allowed_variants: set[str] | None = None) -> pd.DataFrame:
    rows = []
    for v in variant_grid():
        if allowed_variants is not None and v.key not in allowed_variants:
            continue
        x = regime.loc[regime['datetime'].dt.strftime('%H:%M:%S').ge(v.entry_time)].copy()
        x = x.loc[x['bull_regime'] if v.family == 'BULL_PUT' else x['bear_regime']].copy()
        if x.empty:
            continue
        x = x.sort_values(['trade_date','datetime']).drop_duplicates('trade_date', keep='first')
        x['entry_anchor'] = x['datetime'] + pd.Timedelta(minutes=1)
        x['variant_id'] = v.key
        x['family'] = v.family
        x['hold_minutes'] = v.hold_minutes
        x['width_steps'] = v.width_steps
        x['exit_id'] = v.exit_id
        rows.append(x[['variant_id','family','trade_date','datetime','entry_anchor','spot','hold_minutes','width_steps','exit_id','iv_rv']])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()

def select_entries(signals: pd.DataFrame, root: Path) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()
    con = duckdb.connect()
    con.register('signals_df', signals)
    glob = parquet_glob(root)
    sql = f'''
    WITH raw AS (
      SELECT CAST(datetime AS TIMESTAMPTZ) AS ts_utc, CAST(date AS DATE) AS trade_date,
             CAST(expiry AS DATE) AS expiry, expiry_type, option_type,
             CAST(strike_price AS DOUBLE) AS strike, CAST(spot AS DOUBLE) AS spot,
             CAST(open AS DOUBLE) AS open
      FROM read_parquet('{glob}', union_by_name=true)
      WHERE close > 0 AND expiry_type IN ('WEEK','MONTH')
    ),
    expiry_choice AS (
      SELECT s.variant_id, s.trade_date, split_part(s.variant_id,'|',3) AS expiry_type,
             MIN(r.expiry) AS expiry
      FROM signals_df s
      JOIN raw r
        ON r.trade_date=s.trade_date
       AND r.expiry_type=split_part(s.variant_id,'|',3)
       AND r.expiry >= s.trade_date
      GROUP BY s.variant_id, s.trade_date
    ),
    ranked AS (
      SELECT s.*, r.expiry, r.expiry_type, r.option_type, r.strike, r.ts_utc, r.open,
             r.ts_utc + INTERVAL '5 hours 30 minutes' AS local_ts,
             ROW_NUMBER() OVER (
               PARTITION BY s.variant_id, s.trade_date
               ORDER BY ABS(r.strike - CASE WHEN s.family='BULL_PUT' THEN s.spot-3*50.0 ELSE s.spot+3*50.0 END), r.ts_utc
             ) AS rn
      FROM signals_df s
      JOIN expiry_choice e
        ON e.variant_id=s.variant_id AND e.trade_date=s.trade_date
      JOIN raw r
        ON r.trade_date=s.trade_date
       AND r.expiry=e.expiry
       AND r.expiry_type=e.expiry_type
       AND r.option_type=CASE WHEN s.family='BULL_PUT' THEN 'PUT' ELSE 'CALL' END
       AND r.ts_utc + INTERVAL '5 hours 30 minutes' BETWEEN s.entry_anchor AND s.entry_anchor + INTERVAL '2 minutes'
    )
    SELECT * FROM ranked WHERE rn=1
    '''
    short = con.execute(sql).df()
    con.close()
    if short.empty:
        return short
    con = duckdb.connect()
    con.register('short_df', short)
    sql2 = f'''
    WITH raw AS (
      SELECT CAST(datetime AS TIMESTAMPTZ) AS ts_utc, CAST(date AS DATE) AS trade_date,
             CAST(expiry AS DATE) AS expiry, expiry_type, option_type,
             CAST(strike_price AS DOUBLE) AS strike, CAST(open AS DOUBLE) AS open
      FROM read_parquet('{glob}', union_by_name=true)
      WHERE close > 0 AND expiry_type IN ('WEEK','MONTH')
    ),
    ranked AS (
      SELECT s.*, r.strike AS long_strike, r.open AS long_open,
             ROW_NUMBER() OVER (
               PARTITION BY s.variant_id, s.trade_date
               ORDER BY CASE WHEN s.family='BULL_PUT' THEN ABS(r.strike-(s.strike+s.width_steps*-50.0))
                             ELSE ABS(r.strike-(s.strike+s.width_steps*50.0)) END
             ) AS rn2
      FROM short_df s JOIN raw r
        ON r.trade_date=s.trade_date
       AND r.expiry=s.expiry
       AND r.expiry_type=s.expiry_type
       AND r.option_type=s.option_type
       AND r.ts_utc + INTERVAL '5 hours 30 minutes' = s.local_ts
       AND CASE WHEN s.family='BULL_PUT' THEN r.strike < s.strike ELSE r.strike > s.strike END
    )
    SELECT * FROM ranked WHERE rn2=1
    '''
    out = con.execute(sql2).df()
    con.close()
    if out.empty:
        return out
    out['entry_time_local'] = pd.to_datetime(out['local_ts'])
    out['short_entry'] = pd.to_numeric(out['open'], errors='coerce')
    out['long_entry'] = pd.to_numeric(out['long_open'], errors='coerce')
    out['credit'] = out['short_entry'] - out['long_entry']
    return out.loc[out['credit'] > 0].copy()

def simulate(entries: pd.DataFrame, root: Path, out_dir: Path, slippage_points: float) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()
    con = duckdb.connect()
    con.register('entries_df', entries)
    glob = parquet_glob(root)
    sql = f'''
    WITH raw AS (
      SELECT CAST(datetime AS TIMESTAMPTZ) AS ts_utc, CAST(date AS DATE) AS trade_date,
             CAST(expiry AS DATE) AS expiry, expiry_type, option_type,
             CAST(strike_price AS DOUBLE) AS strike, CAST(open AS DOUBLE) AS open, CAST(high AS DOUBLE) AS high,
             CAST(low AS DOUBLE) AS low, CAST(close AS DOUBLE) AS close
      FROM read_parquet('{glob}', union_by_name=true)
      WHERE close > 0 AND expiry_type IN ('WEEK','MONTH')
    )
    SELECT e.*, r.ts_utc + INTERVAL '5 hours 30 minutes' AS local_ts, r.strike, r.open, r.high, r.low, r.close
    FROM entries_df e JOIN raw r
      ON r.trade_date=e.trade_date AND r.expiry=e.expiry AND r.expiry_type=e.expiry_type AND r.option_type=e.option_type
     AND r.strike IN (e.strike,e.long_strike)
     AND r.ts_utc + INTERVAL '5 hours 30 minutes' BETWEEN e.entry_time_local AND e.entry_time_local + e.hold_minutes * INTERVAL '1 minute'
    ORDER BY e.variant_id,e.trade_date,r.strike,r.ts_utc
    '''
    path = con.execute(sql).df()
    con.close()
    if path.empty:
        return pd.DataFrame()
    path['local_ts'] = pd.to_datetime(path['local_ts'])
    cm = OptionCostModel()
    results = []
    for (variant_id, trade_date), g in path.groupby(['variant_id','trade_date'], sort=False):
        meta = g.iloc[0]
        grid = g.pivot_table(index='local_ts', columns='strike', values=['open','high','low','close'], aggfunc='last').sort_index()
        sk, lk = float(meta.strike), float(meta.long_strike)
        if sk not in grid['close'].columns or lk not in grid['close'].columns:
            continue
        entry_t = pd.Timestamp(meta.entry_time_local)
        er = grid.loc[grid.index == entry_t]
        if er.empty: er = grid.iloc[[0]]
        er = er.iloc[0]
        short_entry = float(er[('open',sk)]); long_entry = float(er[('open',lk)])
        credit = short_entry - long_entry
        if credit <= 0: continue
        prof = EXIT_PROFILES[int(meta.exit_id)]
        stop_value = credit * prof['stop_mult']
        target_buyback = credit * (1-prof['target_capture'])
        short_exit = float(grid[('close',sk)].iloc[-1]); long_exit = float(grid[('close',lk)].iloc[-1])
        exit_ts = grid.index[-1]; reason='TIME'
        for ts,row in grid.iterrows():
            sh=float(row[('high',sk)]); sl=float(row[('low',sk)]); lh=float(row[('high',lk)]); ll=float(row[('low',lk)])
            buyback_high = sh-ll; buyback_low=sl-lh
            if buyback_high >= stop_value:
                short_exit=sh; long_exit=ll; exit_ts=ts; reason='STOP'; break
            if buyback_low <= target_buyback:
                short_exit=sl; long_exit=lh; exit_ts=ts; reason='TARGET'; break
        net=cm.vertical_credit_spread_net_pnl(short_entry,long_entry,short_exit,long_exit,nifty_lot_size(trade_date),1,slippage_points)
        results.append({'variant_id':variant_id,'family':meta.family,'trade_date':trade_date,'entry_time':entry_t,'exit_time':exit_ts,'short_strike':sk,'long_strike':lk,'credit':credit,'buyback':short_exit-long_exit,'exit_reason':reason,'net_pnl':net})
    out=pd.DataFrame(results)
    out_dir.mkdir(parents=True,exist_ok=True); out.to_csv(out_dir/'phase9_trades.csv',index=False)
    return out

def leaderboard(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty: return pd.DataFrame()
    rows=[]
    for variant,g in trades.groupby('variant_id',sort=False):
        daily=g.groupby('trade_date').net_pnl.sum(); wins=g.loc[g.net_pnl>0,'net_pnl'].sum(); losses=-g.loc[g.net_pnl<0,'net_pnl'].sum()
        rows.append({'variant_id':variant,'trades':len(g),'active_days':int(daily.size),'mean_active_day_net':float(daily.mean()),'win_rate':float((g.net_pnl>0).mean()),'positive_day_rate':float((daily>0).mean()),'profit_factor':float(wins/losses) if losses>0 else 999.0,'max_drawdown':float((daily.cumsum()-daily.cumsum().cummax()).min()),'total_net':float(g.net_pnl.sum())})
    return pd.DataFrame(rows).sort_values(['mean_active_day_net','profit_factor'],ascending=[False,False]).reset_index(drop=True)

def walk_forward(trades: pd.DataFrame) -> tuple[pd.DataFrame,dict]:
    if trades.empty: return pd.DataFrame(),{'gate':'NO_TRADES'}
    x=trades.copy(); x['trade_date']=pd.to_datetime(x['trade_date']).dt.date; dates=sorted(x.trade_date.unique())
    train_len,val_len,embargo,test_len,step=180,60,5,60,60; rows=[]; start=0
    while start+train_len+val_len+embargo+test_len <= len(dates):
        train_dates=set(dates[start:start+train_len]); val_dates=set(dates[start+train_len:start+train_len+val_len]); test_dates=set(dates[start+train_len+val_len+embargo:start+train_len+val_len+embargo+test_len])
        train=x[x.trade_date.isin(train_dates)]; val=x[x.trade_date.isin(val_dates)]; test=x[x.trade_date.isin(test_dates)]
        scores=[]
        for v,g in train.groupby('variant_id'):
            if len(g)>=8: scores.append((v,float(g.groupby('trade_date').net_pnl.sum().mean())))
        scores.sort(key=lambda z:z[1],reverse=True); val_scores=[]
        for v,_ in scores[:12]:
            g=val[val.variant_id.eq(v)]
            if len(g)>=5: val_scores.append((v,float(g.groupby('trade_date').net_pnl.sum().mean())))
        if not val_scores: start+=step; continue
        val_scores.sort(key=lambda z:z[1],reverse=True); selected=val_scores[0][0]; tg=test[test.variant_id.eq(selected)]
        if tg.empty: start+=step; continue
        daily=tg.groupby('trade_date').net_pnl.sum(); rows.append({'test_start':str(min(test_dates)),'test_end':str(max(test_dates)),'selected_variant':selected,'validation_mean':val_scores[0][1],'test_mean':float(daily.mean()),'test_median':float(daily.median()),'positive_day_rate':float((daily>0).mean()),'trade_days':int(daily.size)}); start+=step
    wf=pd.DataFrame(rows)
    if wf.empty: return wf,{'walk_forward_windows':0,'positive_test_windows':0,'target_windows':0,'mean_test_window_net':None,'gate':'FAIL_PRELIMINARY'}
    return wf,{'walk_forward_windows':int(len(wf)),'positive_test_windows':int((wf.test_mean>0).sum()),'target_windows':int((wf.test_mean>=1000).sum()),'mean_test_window_net':float(wf.test_mean.mean()),'median_test_window_net':float(wf.test_mean.median()),'gate':'PASS_PRELIMINARY' if wf.test_mean.mean()>0 and (wf.test_mean>=1000).any() else 'FAIL_PRELIMINARY'}

def run(root:Path,out:Path,slippage:float,shard_index:int=0,shard_count:int=1)->dict:
    regime=load_regime_series(root)
    allowed=variant_keys_for_shard(shard_index, shard_count)
    signals=build_signals(regime, allowed)
    out.mkdir(parents=True,exist_ok=True)
    signals.to_csv(out/'phase9_signals.csv',index=False); entries=select_entries(signals,root); entries.to_csv(out/'phase9_entries.csv',index=False); trades=simulate(entries,root,out,slippage)
    board=leaderboard(trades); board.to_csv(out/'phase9_leaderboard.csv',index=False); wf,wfs=walk_forward(trades); wf.to_csv(out/'phase9_walk_forward.csv',index=False)
    summary={'variants_preregistered':len(variant_grid()),'signals':int(len(signals)),'entries':int(len(entries)),'trades':int(len(trades)),'target_qualified_prelim':int((board.mean_active_day_net>=1000).sum()) if not board.empty else 0,'slippage_points':slippage,'best':board.iloc[0].to_dict() if not board.empty else None,'walk_forward':wfs,'shard_index':shard_index,'shard_count':shard_count}
    (out/'phase9_summary.json').write_text(json.dumps(summary,indent=2,default=str)); print(json.dumps(summary,indent=2,default=str)); return summary

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--slippage',type=float,default=0.20)
    ap.add_argument('--shard-index',type=int,default=0)
    ap.add_argument('--shard-count',type=int,default=1)
    a=ap.parse_args()
    run(a.data,a.out,a.slippage,a.shard_index,a.shard_count)

if __name__=='__main__': main()