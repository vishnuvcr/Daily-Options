#!/usr/bin/env python3
from pathlib import Path
from datetime import date
import argparse,json
import duckdb,numpy as np,pandas as pd

START=date(2021,7,1); END=date(2026,8,31)
MARKETS=('GSPC','IXIC','N225','HSI','GDAXI','KS11')
HORIZONS=('H10_30','H15_10'); HORIZON_TIMES={'H10_30':'10:30:00','H15_10':'15:10:00'}
WING=200; GLOBAL_THRESHOLD=1.0; GAP_THRESHOLD=.50; NULL_SEEDS=(101,202,303,404,505)

def lot_size(e):
 d=pd.Timestamp(e).date()
 return 50 if d<date(2024,4,26) else 25 if d<date(2024,11,21) else 75 if d<date(2026,1,6) else 65

def charge(price,action,lot,d):
 g=float(price)*lot; stt=g*(.001 if d<date(2026,4,1) else .0015) if action=='SELL' else 0
 ex=g*(.0003503 if d<date(2026,3,1) else .000355299); sebi=g*.000001; stamp=g*.00003 if action=='BUY' else 0
 return 20+.18*(20+ex+sebi)+ex+sebi+stt+stamp

def load_index(root):
 con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'"); p=str(root/'index/NIFTY.parquet').replace(chr(39),chr(39)*2)
 q=f"SELECT CAST(timestamp AS TIMESTAMP) ts,CAST(open AS DOUBLE) open,CAST(close AS DOUBLE) close_px FROM read_parquet('{p}') WHERE CAST(timestamp AS DATE) BETWEEN DATE '{START}' AND DATE '{END}' ORDER BY ts"
 x=con.execute(q).df(); con.close(); x.ts=pd.to_datetime(x.ts); x.rename(columns={'close_px':'close'},inplace=True); x['date']=x.ts.dt.normalize(); x['time']=x.ts.dt.strftime('%H:%M:%S'); return x.drop_duplicates('ts')

def load_global(root):
 out={}
 for m in MARKETS:
  d=pd.read_parquet(root/f'{m}.parquet').sort_values('date').drop_duplicates('date'); d['date']=pd.to_datetime(d.date).dt.normalize(); r=d.close.astype(float).pct_change(); mu=r.shift(1).rolling(60,min_periods=60).mean(); sd=r.shift(1).rolling(60,min_periods=60).std(ddof=1); out[m]=pd.DataFrame({'date':d.date,'z':(r-mu)/sd})
 return out

def build_panel(idx,gd):
 s=idx[idx.time=='09:30:00'][['date','close']].drop_duplicates('date').sort_values('date').copy(); s['date']=pd.to_datetime(s.date).astype('datetime64[ns]'); s.rename(columns={'close':'nifty_spot_0930'},inplace=True)
 daily=idx.groupby('date').close.last().sort_index(); s['prior_close']=[daily.loc[daily.index<d].iloc[-1] if (daily.index<d).any() else np.nan for d in s.date]
 s['gap']=np.log(s.nifty_spot_0930/s.prior_close)
 mu=s.gap.shift(1).rolling(60,min_periods=60).mean(); sd=s.gap.shift(1).rolling(60,min_periods=60).std(ddof=1); s['gap_z']=(s.gap-mu)/sd
 for m,d in gd.items():
  z=d.dropna().rename(columns={'date':'gd','z':f'z_{m}'}); z['gd']=pd.to_datetime(z.gd).astype('datetime64[ns]'); s=pd.merge_asof(s,z.sort_values('gd'),left_on='date',right_on='gd',direction='backward',allow_exact_matches=False); s[f'prior_{m}']=s.gd; s=s.drop(columns=['gd'])
 s['GLOBAL_LEAD']=s[[f'z_{m}' for m in MARKETS]].mean(axis=1); pc=[f'prior_{m}' for m in MARKETS]; s['prior_violations']=s[pc].apply(lambda r:any(pd.notna(v) and v>=s.loc[r.name,'date'] for v in r),axis=1); s['all_prior']=~s.prior_violations
 return s

def state_from_signs(global_lead,gap_z):
 if not np.isfinite(global_lead) or not np.isfinite(gap_z) or abs(global_lead)<GLOBAL_THRESHOLD or abs(gap_z)<GAP_THRESHOLD or global_lead==0 or gap_z==0:return None
 return 'CONVERGENT' if np.sign(global_lead)==np.sign(gap_z) else 'DIVERGENT'

def opt(con,path,ts,strike,typ,field):
 p=str(path).replace(chr(39),chr(39)*2); d=pd.Timestamp(ts); day=d.date(); clock=d.strftime('%H:%M:%S')
 q=f"SELECT CAST({field} AS DOUBLE) px FROM read_parquet('{p}') WHERE CAST(CAST(timestamp AS TIMESTAMP) AS DATE)=DATE '{day}' AND strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S')='{clock}' AND CAST(strike AS DOUBLE)={float(strike)} AND UPPER(CAST(option_type AS VARCHAR))='{typ}' AND {field}>0 ORDER BY CAST(timestamp AS TIMESTAMP) LIMIT 1"
 z=con.execute(q).df(); return None if z.empty else float(z.iloc[0].px)

def attach(p,root):
 files={pd.Timestamp(x.stem).date():x for x in (root/'options/NIFTY').glob('*.parquet')}; exps=sorted(files); p=p.copy(); p['expiry']=[next((e for e in exps if e>=pd.Timestamp(d).date()),None) for d in p.date]; p['atm']=(p.nifty_spot_0930/50).round()*50; p['state']=[state_from_signs(g,gp) for g,gp in zip(p.GLOBAL_LEAD,p.gap_z)]; return p,files

def signal_panel(p,null_seed=None):
 x=p.copy(); cols=[f'z_{m}' for m in MARKETS]
 if null_seed is not None:
  rng=np.random.default_rng(null_seed); order=rng.permutation(len(x)); block=x[cols].to_numpy(copy=True); x[cols]=block[order,:]; x['GLOBAL_LEAD']=x[cols].mean(axis=1); x['state']=[state_from_signs(g,gp) for g,gp in zip(x.GLOBAL_LEAD,x.gap_z)]
 else:
  x['state']=[state_from_signs(g,gp) for g,gp in zip(x.GLOBAL_LEAD,x.gap_z)]
 x=x[x.state.notna()].copy(); return pd.concat([x.assign(horizon=h) for h in HORIZONS],ignore_index=True)

def direction(row):
 return 1 if (row.state=='CONVERGENT' and row.GLOBAL_LEAD>0) or (row.state=='DIVERGENT' and row.GLOBAL_LEAD<0) else -1

def trade(r,con,files,slip):
 d=pd.Timestamp(r.date).date(); e=r.expiry; direction_sign=direction(r); typ='CE' if direction_sign>0 else 'PE'; atm=int(r.atm); wing=atm+WING if typ=='CE' else atm-WING; ex=HORIZON_TIMES[r.horizon]; path=files[e]; lot=lot_size(e); raw=sl=tc=0
 for k,a in [(atm,'BUY'),(wing,'SELL')]:
  ep=opt(con,path,f'{d} 09:31:00',k,typ,'open'); xp=opt(con,path,f'{d} {ex}',k,typ,'close')
  if ep is None or xp is None:return None
  raw+=(xp-ep)*lot if a=='BUY' else (ep-xp)*lot; sl+=2*slip*lot; tc+=charge(ep+slip if a=='BUY' else max(0,ep-slip),a,lot,d)+charge(max(0,xp-slip) if a=='BUY' else xp+slip,'SELL' if a=='BUY' else 'BUY',lot,d)
 return {'day':str(d),'state':r.state,'horizon':r.horizon,'direction':direction_sign,'raw_gross':raw,'slippage_cost':sl,'transaction_costs':tc,'net_pnl':raw-sl-tc}

def summarize(t):
 rows=[]
 for st in ('CONVERGENT','DIVERGENT'):
  for h in HORIZONS:
   g=t[(t.state==st)&(t.horizon==h)] if not t.empty else t.iloc[0:0]
   if g.empty: rows.append({'state':st,'horizon':h,'trades':0,'weeks':0,'total_net':0.0,'mean_weekly_net':0.0,'median_weekly_net':0.0,'positive_week_rate':0.0}); continue
   w=g.assign(week=pd.to_datetime(g.day).dt.to_period('W-SUN').astype(str)).groupby('week').net_pnl.sum(); eq=w.sort_index().cumsum(); dd=(eq-eq.cummax()).min()
   rows.append({'state':st,'horizon':h,'trades':len(g),'weeks':len(w),'total_net':g.net_pnl.sum(),'mean_weekly_net':w.mean(),'median_weekly_net':w.median(),'positive_week_rate':(w>0).mean(),'worst_trade':g.net_pnl.min(),'worst_week':w.min(),'max_drawdown':dd,'raw_gross':g.raw_gross.sum(),'total_slippage':g.slippage_cost.sum(),'total_transaction_costs':g.transaction_costs.sum()})
 return pd.DataFrame(rows)

def run(a):
 root=Path(a.data); out=Path(a.out); out.mkdir(parents=True,exist_ok=True); idx=load_index(root); gd=load_global(Path(a.global_data)); p=build_panel(idx,gd); p,files=attach(p,root)
 global_ready=p[[f'z_{m}' for m in MARKETS]].notna().all(axis=1)&p.all_prior; full_ready=global_ready&p.gap_z.notna(); cov=float(full_ready.sum()/global_ready.sum()) if global_ready.sum() else 0
 gate={'status':'PASS' if global_ready.any() and cov>=.95 and int(p.prior_violations.sum())==0 else 'FAIL','raw_sessions':len(p),'global_feature_eligible_sessions':int(global_ready.sum()),'full_feature_eligible_sessions':int(full_ready.sum()),'coverage':cov,'prior_violations':int(p.prior_violations.sum()),'warmup_or_global_unavailable_sessions':int((~global_ready).sum()),'gap_warmup_sessions':int(global_ready.sum()-full_ready.sum()),'study_start':str(START),'study_end':str(END)}
 (out/'data_gate.json').write_text(json.dumps(gate,indent=2,default=str)); p.to_csv(out/'feature_panel.csv',index=False)
 if a.gate_only or gate['status']!='PASS':print(json.dumps(gate));return
 s=signal_panel(p); (out/'signal_counts.csv').write_text(s.groupby(['state','horizon']).size().reset_index(name='signals').to_csv(index=False))
 con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'"); covs=[]
 for st in ('CONVERGENT','DIVERGENT'):
  for h in HORIZONS:
   q=s[(s.state==st)&(s.horizon==h)]; complete=0
   for r in q.itertuples(index=False):
    d=pd.Timestamp(r.date).date(); e=r.expiry; typ='CE' if direction(r)>0 else 'PE'; atm=int(r.atm); wing=atm+WING if typ=='CE' else atm-WING
    vals=[opt(con,files[e],f'{d} 09:31:00',atm,typ,'open'),opt(con,files[e],f'{d} 09:31:00',wing,typ,'open'),opt(con,files[e],f'{d} {HORIZON_TIMES[h]}',atm,typ,'close'),opt(con,files[e],f'{d} {HORIZON_TIMES[h]}',wing,typ,'close')]; complete+=int(all(v is not None for v in vals))
   covs.append({'state':st,'horizon':h,'candidate_rows':len(q),'complete_quote_rows':complete,'coverage':complete/len(q) if len(q) else 0})
 (out/'execution_coverage.json').write_text(json.dumps(covs,indent=2))
 if any(x['coverage']<.95 for x in covs):
  gate['status']='FAIL_EXECUTION_COVERAGE'; gate['execution_coverage']=covs; (out/'data_gate.json').write_text(json.dumps(gate,indent=2)); print(json.dumps(gate)); return
 for fr,slip in [('base',.20),('stress',.40)]:
  rows=[]
  for r in s.itertuples(index=False):
   x=trade(r,con,files,slip)
   if x: rows.append(x)
  t=pd.DataFrame(rows); t.to_csv(out/f'trades_{fr}.csv',index=False); summarize(t).to_csv(out/f'true_cell_summary_{fr}.csv',index=False)
  null=[]
  for seed in NULL_SEEDS:
   ns=signal_panel(p,seed)
   for r in ns.itertuples(index=False):
    x=trade(r,con,files,slip)
    if x: x['null_seed']=seed; null.append(x)
  nd=pd.DataFrame(null); nd.to_csv(out/f'null_trades_{fr}.csv',index=False); pd.concat([summarize(nd[nd.null_seed==seed]).assign(null_seed=seed) for seed in NULL_SEEDS],ignore_index=True).to_csv(out/f'null_summary_{fr}.csv',index=False)
 con.close(); print(json.dumps(gate))

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data',default='data/cache/phase31_trademarkk'); ap.add_argument('--global-data',default='data/cache/phase31_8_global'); ap.add_argument('--out',default='reports/phase37/base'); ap.add_argument('--slippage',type=float,default=.20); ap.add_argument('--gate-only',action='store_true'); a=ap.parse_args(); run(a)
if __name__=='__main__':main()
