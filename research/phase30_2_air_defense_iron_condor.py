#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from datetime import date
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd

START_DATE = date(2025, 9, 2)
END_DATE = date(2026, 8, 4)
VIX_REL_PATH = Path('vix/india_vix.csv')
ENTRY_OFFSETS = (-2, -3)
ENTRY_CLOCKS = ('09:30:00', '10:00:00')
SIGMAS = (1.0, 2.0)
WING_WIDTHS = (100.0, 200.0, 300.0)
BROKERAGE_PER_ORDER = 10.0
WEEKLY_TARGET = 5000.0
POSITIVE_WEEK_RATE_TARGET = 0.70
EXECUTION_COVERAGE_TARGET = 0.80
EXIT_MINUTES_BEFORE_EXPIRY = 5
BASE_SLIPPAGE = 0.20
STRESS_SLIPPAGE = 0.40

def expected_move(spot, vix, minutes_to_exit, sigma):
    if min(spot, vix, minutes_to_exit, sigma) <= 0:
        raise ValueError('invalid expected-move inputs')
    return float(spot * (vix / 100.0) * math.sqrt(minutes_to_exit / (365.0 * 24.0 * 60.0)) * sigma)

def select_call_strike(strikes, spot, move):
    return next((float(s) for s in sorted(strikes) if float(s) >= spot + move), None)

def select_put_strike(strikes, spot, move):
    return next((float(s) for s in sorted(strikes, reverse=True) if float(s) <= spot - move), None)

def lot_size(expiry):
    d = pd.Timestamp(expiry).date()
    if d < date(2024, 4, 26):
        return 50
    if d < date(2024, 11, 21):
        return 25
    if d < date(2026, 1, 6):
        return 75
    return 65

def order_cost(price, side, qty, lot, order_date, brokerage):
    gross = float(price) * qty * lot
    stt_rate = 0.001 if order_date < date(2026, 4, 1) else 0.0015
    exchange_rate = 0.0003503 if order_date < date(2026, 3, 1) else 0.000355299
    sebi = gross * 0.000001
    exchange = gross * exchange_rate
    stt = gross * stt_rate if side == 'SELL' else 0.0
    stamp = gross * 0.00003 if side == 'BUY' else 0.0
    gst = 0.18 * (brokerage + exchange + sebi)
    return brokerage + exchange + sebi + stt + stamp + gst

def execution_cash(price, side, qty, lot, slippage):
    if side == 'SELL':
        return (price - slippage) * qty * lot
    return -(price + slippage) * qty * lot

def load_vix(root):
    p = Path(root) / VIX_REL_PATH
    x = pd.read_csv(p)
    x['date'] = pd.to_datetime(x['date']).dt.date
    x['close'] = pd.to_numeric(x['close'], errors='coerce')
    return x.dropna(subset=['date','close']).drop_duplicates('date').sort_values('date')

def previous_vix(vix, d):
    x = vix[vix['date'] < d]
    return None if x.empty else float(x.iloc[-1]['close'])

def expiry_files(root):
    out = []
    for p in sorted((Path(root) / 'options' / 'NIFTY').glob('*.parquet')):
        try:
            d = pd.Timestamp(p.stem).date()
        except Exception:
            continue
        if START_DATE <= d <= END_DATE and d.weekday() == 1:
            out.append((d, p))
    return out

def session_dates(con, index_path):
    q = f'''SELECT DISTINCT CAST(trading_day AS DATE) AS d FROM read_parquet('{str(index_path).replace(chr(39), chr(39)+chr(39))}') WHERE CAST(trading_day AS DATE) BETWEEN DATE '2025-08-01' AND DATE '2026-08-04' ORDER BY d'''
    x = con.execute(q).df()
    return [pd.Timestamp(v).date() for v in x['d'].tolist()]

def session_offset(sessions, expiry, offset):
    prior = [d for d in sessions if d < expiry]
    idx = len(prior) + offset
    return None if idx < 0 or idx >= len(prior) else prior[idx]

def load_spot(con, index_path, start_ts, end_ts):
    q = f'''SELECT CAST(timestamp AS TIMESTAMP) AS ts, CAST(close AS DOUBLE) AS close_px FROM read_parquet('{str(index_path).replace(chr(39), chr(39)+chr(39))}') WHERE CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{start_ts}' AND TIMESTAMP '{end_ts}' ORDER BY ts'''
    x = con.execute(q).df()
    if x.empty:
        return x
    x['ts'] = pd.to_datetime(x['ts']).dt.floor('min')
    return x.drop_duplicates('ts').sort_values('ts')

def available_strikes(con, path, side):
    q = f'''SELECT DISTINCT CAST(strike AS DOUBLE) AS strike FROM read_parquet('{str(path).replace(chr(39), chr(39)+chr(39))}') WHERE UPPER(CAST(option_type AS VARCHAR))='{side}' AND close > 0'''
    x = con.execute(q).df()
    return sorted(float(v) for v in x['strike'].dropna().tolist())

def load_option_series(con, path, strike, side, start_ts, end_ts):
    q = f'''SELECT CAST(timestamp AS TIMESTAMP) AS ts, CAST(open AS DOUBLE) AS open_px, CAST(close AS DOUBLE) AS close_px FROM read_parquet('{str(path).replace(chr(39), chr(39)+chr(39))}') WHERE CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{start_ts}' AND TIMESTAMP '{end_ts}' AND CAST(strike AS DOUBLE)={float(strike)} AND UPPER(CAST(option_type AS VARCHAR))='{side}' AND close > 0 ORDER BY ts'''
    x = con.execute(q).df()
    if x.empty:
        return pd.DataFrame(columns=['ts','open_px','close_px'])
    x['ts'] = pd.to_datetime(x['ts']).dt.floor('min')
    return x.drop_duplicates('ts').sort_values('ts')

def price_at(series, ts):
    z = series[series['ts'] >= pd.Timestamp(ts)]
    if z.empty:
        return None
    v = z.iloc[0]['open_px']
    return None if pd.isna(v) or v <= 0 else float(v)

def mark_at(series, ts):
    z = series[series['ts'] <= pd.Timestamp(ts)]
    if z.empty:
        return None
    v = z.iloc[-1]['close_px']
    return None if pd.isna(v) or v <= 0 else float(v)

def build_setup(con, index_path, expiry_path, expiry, entry_date, entry_clock, sigma, wing_width, strike_cache, vix):
    signal_ts = pd.Timestamp(f'{entry_date} {entry_clock}')
    fill_ts = signal_ts + pd.Timedelta(minutes=1)
    exit_ref = pd.Timestamp(expiry) + pd.Timedelta(hours=15, minutes=25)
    if exit_ref <= fill_ts:
        return None
    spot_series = load_spot(con, index_path, f'{entry_date} 09:00:00', f'{expiry} 15:26:00')
    s = spot_series[spot_series['ts'] <= signal_ts]
    if s.empty:
        return None
    spot = float(s.iloc[-1]['close_px'])
    vix_value = previous_vix(vix, entry_date)
    if vix_value is None:
        return None
    key = str(expiry_path)
    if key not in strike_cache:
        strike_cache[key] = {
            'CE': available_strikes(con, expiry_path, 'CE'),
            'PE': available_strikes(con, expiry_path, 'PE'),
        }
    strikes = strike_cache[key]
    minutes = (exit_ref - signal_ts).total_seconds() / 60.0
    move = expected_move(spot, vix_value, minutes, sigma)
    ce = select_call_strike(strikes['CE'], spot, move)
    pe = select_put_strike(strikes['PE'], spot, move)
    if ce is None or pe is None:
        return None
    ce_long = select_call_strike(strikes['CE'], ce, wing_width)
    pe_long = select_put_strike(strikes['PE'], pe, wing_width)
    if ce_long is None or pe_long is None:
        return None
    ce_series = load_option_series(con, expiry_path, ce, 'CE', fill_ts, exit_ref + pd.Timedelta(minutes=1))
    pe_series = load_option_series(con, expiry_path, pe, 'PE', fill_ts, exit_ref + pd.Timedelta(minutes=1))
    ce_long_series = load_option_series(con, expiry_path, ce_long, 'CE', fill_ts, exit_ref + pd.Timedelta(minutes=1))
    pe_long_series = load_option_series(con, expiry_path, pe_long, 'PE', fill_ts, exit_ref + pd.Timedelta(minutes=1))
    series = {'short_CE': ce_series, 'short_PE': pe_series, 'long_CE': ce_long_series, 'long_PE': pe_long_series}
    if any(z.empty for z in series.values()):
        return None
    if any(price_at(z, fill_ts) is None for z in series.values()):
        return None
    return {
        'expiry': expiry, 'entry_date': entry_date, 'entry_clock': entry_clock,
        'signal_ts': signal_ts, 'fill_ts': fill_ts, 'exit_ref': exit_ref,
        'spot': spot, 'vix': vix_value, 'sigma': sigma, 'wing_width': wing_width,
        'expected_move': move,
        'strikes': {'short_CE': ce, 'short_PE': pe, 'long_CE': ce_long, 'long_PE': pe_long},
        'series': series, 'spot_series': spot_series, 'lot': lot_size(expiry),
    }

def simulate_trade(setup, slippage, brokerage):
    lot = setup['lot']
    cash = 0.0
    costs = 0.0
    entry_ts = setup['fill_ts']
    exit_ref = setup['exit_ref']

    opening = [
        ('short_CE', 'SELL'),
        ('short_PE', 'SELL'),
        ('long_CE', 'BUY'),
        ('long_PE', 'BUY'),
    ]
    for name, side in opening:
        px = price_at(setup['series'][name], entry_ts)
        if px is None:
            return None
        cash += execution_cash(px, side, 1, lot, slippage)
        costs += order_cost(px, side, 1, lot, entry_ts.date(), brokerage)

    exit_ts = exit_ref + pd.Timedelta(minutes=1)
    closing = [
        ('short_CE', 'BUY'),
        ('short_PE', 'BUY'),
        ('long_CE', 'SELL'),
        ('long_PE', 'SELL'),
    ]
    for name, side in closing:
        px = price_at(setup['series'][name], exit_ts)
        if px is None:
            px = mark_at(setup['series'][name], exit_ref)
        if px is None:
            return None
        cash += execution_cash(px, side, 1, lot, slippage)
        costs += order_cost(px, side, 1, lot, exit_ts.date(), brokerage)

    return {
        'expiry': str(setup['expiry']),
        'entry_date': str(setup['entry_date']),
        'entry_clock': setup['entry_clock'],
        'sigma': setup['sigma'],
        'wing_width': setup['wing_width'],
        'spot': setup['spot'],
        'vix': setup['vix'],
        'expected_move': setup['expected_move'],
        'short_ce_strike': setup['strikes']['short_CE'],
        'short_pe_strike': setup['strikes']['short_PE'],
        'long_ce_strike': setup['strikes']['long_CE'],
        'long_pe_strike': setup['strikes']['long_PE'],
        'lot': lot,
        'costs': float(costs),
        'net_pnl': float(cash - costs),
    }

def max_drawdown(values):
    a = np.asarray(values, dtype=float)
    if a.size == 0: return 0.0
    eq = np.cumsum(a)
    peaks = np.maximum.accumulate(np.r_[0.0, eq])
    return float(np.max(peaks[1:] - eq))

def profit_factor(values):
    a = np.asarray(values, dtype=float)
    wins = float(a[a > 0].sum())
    losses = float(-a[a < 0].sum())
    if losses == 0: return float('inf') if wins > 0 else 0.0
    return wins / losses

def expected_shortfall(values, alpha=0.95):
    a = np.asarray(values, dtype=float)
    if a.size == 0: return 0.0
    q = float(np.quantile(a, 1-alpha))
    tail = a[a <= q]
    return float(tail.mean()) if tail.size else q

def run(data_root, out_root, slippage, brokerage):
    root = Path(data_root)
    index_path = root / 'index' / 'NIFTY.parquet'
    vix = load_vix(root)
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    sessions = session_dates(con, index_path)
    files = expiry_files(root)
    strike_cache = {}
    rows = []
    for expiry, path in files:
        for offset in ENTRY_OFFSETS:
            entry_date = session_offset(sessions, expiry, offset)
            if entry_date is None:
                continue
            for clock in ENTRY_CLOCKS:
                for sigma in SIGMAS:
                    for wing_width in WING_WIDTHS:
                        setup = build_setup(con, index_path, path, expiry, entry_date, clock, sigma, wing_width, strike_cache, vix)
                        if setup is None:
                            continue
                        setup['entry_offset'] = offset
                        result = simulate_trade(setup, slippage, brokerage)
                        if result is None:
                            continue
                        result['entry_offset'] = offset
                        result['cell_id'] = f"IC30_{abs(offset):02d}_{clock.replace(':','')}_S{int(sigma)}_W{int(wing_width)}"
                        rows.append(result)
    con.close()
    trades = pd.DataFrame(rows)
    out = Path(out_root)
    out.mkdir(parents=True, exist_ok=True)
    coverage = {
        'eligible_expiry_files': len(files), 'vix_rows': int(len(vix)),
        'research_window': [str(START_DATE), str(END_DATE)], 'normal_tuesday_only': True,
    }
    if trades.empty:
        summary = {'status':'NO_RESULTS','slippage':slippage,'brokerage':brokerage,'coverage':coverage}
        (out/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        return summary
    key_cols = ['expiry','entry_offset','entry_clock','sigma','wing_width']
    dup = int(trades.duplicated(key_cols).sum())
    if dup:
        raise RuntimeError(f'duplicate setup keys: {dup}')
    trades.to_csv(out/'trades.csv', index=False)
    group_cols = ['cell_id','entry_offset','entry_clock','sigma','wing_width']
    board = trades.groupby(group_cols, dropna=False).agg(
        executed_weeks=('net_pnl','size'), mean_weekly_net=('net_pnl','mean'),
        median_weekly_net=('net_pnl','median'), positive_week_rate=('net_pnl',lambda x:float((x>0).mean())),
        total_net=('net_pnl','sum'), worst_week=('net_pnl','min')
    ).reset_index()
    extra=[]
    for keys,g in trades.groupby(group_cols, dropna=False, sort=False):
        vals=g['net_pnl'].to_numpy(float)
        extra.append({
            'cell_id':keys[0], 'entry_offset':int(keys[1]), 'entry_clock':keys[2], 'sigma':float(keys[3]), 'wing_width':float(keys[4]),
            'profit_factor':profit_factor(vals), 'weekly_max_drawdown':max_drawdown(vals), 'expected_shortfall_95':expected_shortfall(vals),
        })
    board=board.merge(pd.DataFrame(extra),on=group_cols,how='left')
    board['executed_week_coverage']=board['executed_weeks']/max(len(files),1)
    board['target_pass_mean']=board['mean_weekly_net']>=WEEKLY_TARGET
    board['target_pass_median']=board['median_weekly_net']>=WEEKLY_TARGET
    board['target_pass_positive_rate']=board['positive_week_rate']>=POSITIVE_WEEK_RATE_TARGET
    board['target_pass_execution_coverage']=board['executed_week_coverage']>=EXECUTION_COVERAGE_TARGET
    board['preliminary_pass']=board[['target_pass_mean','target_pass_median','target_pass_positive_rate','target_pass_execution_coverage']].all(axis=1)
    board.to_csv(out/'leaderboard.csv', index=False)
    trades['year']=pd.to_datetime(trades['expiry']).dt.year
    trades.groupby(['cell_id','year']).agg(weeks=('net_pnl','size'),mean_weekly_net=('net_pnl','mean'),median_weekly_net=('net_pnl','median'),positive_week_rate=('net_pnl',lambda x:float((x>0).mean())),total_net=('net_pnl','sum'),worst_week=('net_pnl','min')).reset_index().to_csv(out/'yearly.csv',index=False)
    trades.sort_values(['cell_id','expiry']).to_csv(out/'weekly.csv',index=False)
    best=board.sort_values(['mean_weekly_net','median_weekly_net'],ascending=False).iloc[0].to_dict()
    summary={'status':'COMPLETE','slippage':slippage,'brokerage':brokerage,'cell_count':int(board['cell_id'].nunique()),'reference_position_size':'1 NIFTY lot each on short CE, short PE, long CE and long PE','weekly_target':WEEKLY_TARGET,'preliminary_pass_cells':int(board['preliminary_pass'].sum()),'duplicate_setup_keys':dup,'best':best,'coverage':coverage}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,default=str),encoding='utf-8')
    return summary

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--slippage',type=float,required=True)
    ap.add_argument('--brokerage',type=float,default=BROKERAGE_PER_ORDER)
    a=ap.parse_args()
    print(json.dumps(run(a.data,a.out,a.slippage,a.brokerage),indent=2,default=str))
