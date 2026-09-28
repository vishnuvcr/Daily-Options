#!/usr/bin/env python3
from pathlib import Path
from datetime import date
import argparse,json,math
import duckdb,numpy as np,pandas as pd

START=date(2021,7,1); END=date(2026,8,31)
MARKETS=('GSPC','IXIC','N225','HSI','GDAXI','KS11')
STATES=('LOW_VOL_STATE','HIGH_VOL_STATE'); HORIZONS=('H10_30','H15_10')
HORIZON_TIMES={'H10_30':'10:30:00','H15_10':'15:10:00'}; NULL_SEEDS=(101,202,303,404,505)
THRESHOLD=1.0; WING=200

def lot_size(e):
 d=pd.Timestamp(e).date()
 return 50 if d<date(2024,4,26) else 25 if d<date(2024,11,21) else 75 if d<date(2026,1,6) else 65

def charge(price,action,lot,d):
 g=float(price)*lot; stt=g*(.001 if d<date(2026,4,1) else .0015) if action=='SELL' else 0
 ex=g*(.0003503 if d<date(2026,3,1) else .000355299); sebi=g*.000001; stamp=g*.00003 if action=='BUY' else 0
 return 20+.18*(20+ex+sebi)+ex+sebi+stt+stamp

def index(root):
 con=duckdb.connect(); p=str(root/'index/NIFTY.parquet').replace(chr(39),chr(39)*2)
 q=f"SELECT CAST(timestamp AS TIMESTAMP) ts,CAST(open AS DOUBLE) open,CAST(high AS DOUBLE) high,CAST(low AS DOUBLE) low,CAST(close AS DOUBLE) close_px FROM read_parquet('{p}') WHERE CAST(timestamp AS DATE) BETWEEN DATE '{START}' AND DATE '{END}' ORDER BY ts"
 x=con.execute(q).df(); con.close(); x.rename(columns={'close_px':'close'},inplace=True); x.ts=pd.to_datetime(x.ts); x['date']=x.ts.dt.normalize(); x['time']=x.ts.dt.strftime('%H:%M:%S'); return x.drop_duplicates('ts')

def globals_(root):
 out={}
 for m in MARKETS:
  d=pd.read_parquet(root/f'{m}.parquet').sort_values('date').drop_duplicates('date'); d['date']=pd.to_datetime(d.date).dt.normalize(); r=d.close.astype(float).pct_change(); mu=r.shift(1).rolling(60,min_periods=60).mean(); sd=r.shift(1).rolling(60,min_periods=60).std(ddof=1); out[m]=pd.DataFrame({'date':d.date,'z':(r-mu)/sd})
 return out

def global_panel(idx,gd):
 s=idx[idx.time=='09:30:00'][['date','open']].drop_duplicates('date').sort_values('date').copy(); s.rename(columns={'open':'nifty_open_0930'},inplace=True); s['date']=pd.to_datetime(s['date']).astype('datetime64[ns]')
 for m,d in gd.items():
  z=d.dropna().rename(columns={'date':'gd','z':f'z_{m}'}); z['gd']=pd.to_datetime(z['gd']).astype('datetime64[ns]'); s=pd.merge_asof(s,z.sort_values('gd'),left_on='date',right_on='gd',direction='backward',allow_exact_matches=False); s[f'prior_{m}']=s.gd; s=s.drop(columns=['gd'])
 s['GLOBAL_LEAD']=s[[f'z_{m}' for m in MARKETS]].mean(axis=1); pc=[f'prior_{m}' for m in MARKETS]; s['prior_violations']=s[pc].apply(lambda r:any(pd.notna(v) and v>=s.loc[r.name,'date'] for v in r),axis=1); s['all_prior']=~s['prior_violations']; return s

def opt(con,path,ts,strike,typ,field):
 p=str(path).replace(chr(39),chr(39)*2); q=f"SELECT CAST({field} AS DOUBLE) px FROM read_parquet('{p}') WHERE CAST(timestamp AS TIMESTAMP)=TIMESTAMP '{ts}' AND CAST(strike AS DOUBLE)={float(strike)} AND UPPER(CAST(option_type AS VARCHAR))='{typ}' AND {field}>0 LIMIT 1"; z=con.execute(q).df(); return None if z.empty else float(z.iloc[0].px)

def opt_latest(con,path,cutoff,strike,typ,field):
 p=str(path).replace(chr(39),chr(39)*2); q=f"SELECT CAST({field} AS DOUBLE) px,CAST(timestamp AS TIMESTAMP) ts FROM read_parquet('{p}') WHERE CAST(timestamp AS TIMESTAMP)<=TIMESTAMP '{cutoff}' AND CAST(strike AS DOUBLE)={float(strike)} AND UPPER(CAST(option_type AS VARCHAR))='{typ}' AND {field}>0 ORDER BY ts DESC LIMIT 1"; z=con.execute(q).df(); return None if z.empty else float(z.iloc[0].px)

def bs(s,k,t,v):
 if t<=0:return max(s-k,0)
 d1=(math.log(s/k)+.5*v*v*t)/(v*math.sqrt(t)); d2=d1-v*math.sqrt(t); n=lambda x:.5*(1+math.erf(x/math.sqrt(2))); return s*n(d1)-k*n(d2)

def iv(s,k,t,target):
 if min(s,k,t,target)<=0:return None
 lo,hi=1e-6,5
 for _ in range(80):
  mid=(lo+hi)/2; val=2*bs(s,k,t,mid)-s+k
  if val<target:lo=mid
  else:hi=mid
 return (lo+hi)/2

def local_state(idx,root,files):
 daily=idx.groupby('date').agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last')).sort_index(); con=duckdb.connect(); rows=[]
 for day in daily.index:
  prev=daily.loc[daily.index<day]
  if len(prev)<20:continue
  rv=float(prev.tail(20).close.pct_change().dropna().std(ddof=1)*math.sqrt(252)*100); pdx=prev.index[-1]; e=next((e for e in sorted(files) if e>=pdx.date()),None)
  if e is None:continue
  spot=float(prev.loc[pdx,'close']); atm=round(spot/50)*50; path=files[e]; ts=f'{pdx.date()} 15:30:00'; ce=opt_latest(con,path,ts,atm,'CE','close'); pe=opt_latest(con,path,ts,atm,'PE','close')
  if ce is None or pe is None:continue
  t=max((pd.Timestamp(f'{e} 15:30:00')-pd.Timestamp(ts)).total_seconds()/31536000,1/31536000); ivv=iv(spot,atm,t,ce+pe)
  if ivv is not None:rows.append({'date':day,'prior_iv':ivv*100,'prior_rv':rv,'iv_rv_gap':ivv*100-rv})
 con.close(); x=pd.DataFrame(rows)
 if x.empty:return x
 x=x.sort_values('date'); mu=x.iv_rv_gap.shift(1).rolling(60,min_periods=60).mean(); sd=x.iv_rv_gap.shift(1).rolling(60,min_periods=60).std(ddof=1); x['iv_rv_z']=(x.iv_rv_gap-mu)/sd; x['state']=np.select([x.iv_rv_z<=-.75,x.iv_rv_z>=.75],STATES,'NEUTRAL'); return x

def summarize(t):
 rows=[]
 for st in STATES:
  for h in HORIZONS:
   g=t[(t.state==st)&(t.horizon==h)] if not t.empty else t.iloc[0:0]
   if g.empty:rows.append({'state':st,'horizon':h,'trades':0,'weeks':0,'total_net':0.0,'mean_weekly_net':0.0,'median_weekly_net':0.0,'positive_week_rate':0.0});continue
   w=g.assign(week=pd.to_datetime(g.day).dt.to_period('W-SUN').astype(str)).groupby('week').net_pnl.sum(); eq=w.sort_index().cumsum(); dd=(eq-eq.cummax()).min()
   rows.append({'state':st,'horizon':h,'trades':len(g),'weeks':len(w),'total_net':g.net_pnl.sum(),'mean_weekly_net':w.mean(),'median_weekly_net':w.median(),'positive_week_rate':(w>0).mean(),'worst_trade':g.net_pnl.min(),'worst_week':w.min(),'max_drawdown':dd,'total_slippage':g.slippage_cost.sum(),'total_transaction_costs':g.transaction_costs.sum(),'raw_gross':g.raw_gross.sum()})
 return pd.DataFrame(rows)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data',default='data/cache/phase31_trademarkk'); ap.add_argument('--global-data',default='data/cache/phase31_8_global'); ap.add_argument('--out',default='reports/phase35'); ap.add_argument('--slippage',type=float,default=.20); ap.add_argument('--gate-only',action='store_true'); a=ap.parse_args(); root=Path(a.data); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
 idx=index(root); gp=global_panel(idx,globals_(Path(a.global_data))); files={pd.Timestamp(p.stem).date():p for p in (root/'options/NIFTY').glob('*.parquet')}; loc=local_state(idx,root,files); p=gp.merge(loc,on='date',how='left')
 global_ready=p[[f'z_{m}' for m in MARKETS]].notna().all(axis=1)&p.all_prior; ready=global_ready&p.iv_rv_z.notna(); cov=float(ready.sum()/global_ready.sum()) if global_ready.sum() else 0.0; gate={'status':'PASS' if cov>=.95 and global_ready.any() and int(p.prior_violations.sum())==0 else 'FAIL','raw_sessions':len(p),'global_feature_eligible_sessions':int(global_ready.sum()),'feature_eligible_sessions':int(ready.sum()),'coverage':cov,'prior_violations':int(p.prior_violations.sum()),'warmup_or_global_unavailable_sessions':int((~global_ready).sum()),'threshold':THRESHOLD,'study_start':str(START),'study_end':str(END)}; (out/'data_gate.json').write_text(json.dumps(gate,indent=2,default=str)); p.to_csv(out/'feature_panel.csv',index=False)
 if a.gate_only or gate['status']!='PASS':print(json.dumps(gate));return
 s=p[(p.GLOBAL_LEAD.abs()>=THRESHOLD)&p.state.isin(STATES)].copy(); s=pd.concat([s.assign(horizon=h) for h in HORIZONS],ignore_index=True); (out/'signal_counts.json').write_text(json.dumps({'candidate_days':int(len(s)/2),'candidate_rows':int(len(s)),'low_state_days':int((s.state=='LOW_VOL_STATE').sum()/2),'high_state_days':int((s.state=='HIGH_VOL_STATE').sum()/2),'global_abs_trigger_days':int((p.GLOBAL_LEAD.abs()>=THRESHOLD).sum())},indent=2)); files_list=sorted(files); con=duckdb.connect(); cov=[]
 for st in STATES:
  for h in HORIZONS:
   q=s[(s.state==st)&(s.horizon==h)]; complete=0
   for rr in q.itertuples(index=False):
    dd=pd.Timestamp(rr.date).date(); ee=next((z for z in files_list if z>=dd),None); tt='CE' if rr.GLOBAL_LEAD>0 else 'PE'; aa=round(float(rr.nifty_open_0930)/50)*50; ww=aa+WING if tt=='CE' else aa-WING; ex=HORIZON_TIMES[h]
    req=[opt(con,files[ee],f'{dd} 09:31:00',aa,tt,'open'),opt(con,files[ee],f'{dd} 09:31:00',ww,tt,'open'),opt(con,files[ee],f'{dd} {ex}',aa,tt,'close'),opt(con,files[ee],f'{dd} {ex}',ww,tt,'close')]
    complete+=int(all(v is not None for v in req))
   cov.append({'state':st,'horizon':h,'candidate_rows':len(q),'complete_quote_rows':complete,'coverage':complete/len(q) if len(q) else 0.0})
 (out/'execution_coverage.json').write_text(json.dumps(cov,indent=2)); con.close();
 if any(x['coverage']<.95 for x in cov):
  gate['status']='FAIL_EXECUTION_COVERAGE'; gate['execution_coverage']=cov; (out/'data_gate.json').write_text(json.dumps(gate,indent=2,default=str)); print(json.dumps(gate)); return
 con=duckdb.connect(); rows=[]
 for r in s.itertuples(index=False):
  d=pd.Timestamp(r.date).date(); e=next((e for e in sorted(files) if e>=d),None); typ='CE' if r.GLOBAL_LEAD>0 else 'PE'; atm=round(float(r.nifty_open_0930)/50)*50; wing=atm+WING if typ=='CE' else atm-WING; ex=HORIZON_TIMES[r.horizon]; lot=lot_size(e); path=files[e]; raw=sl=tc=0; ok=True
  for k,act in [(atm,'BUY'),(wing,'SELL')]:
   ep=opt(con,path,f'{d} 09:31:00',k,typ,'open'); xp=opt(con,path,f'{d} {ex}',k,typ,'close');
   if ep is None or xp is None:ok=False;break
   raw+=(xp-ep)*lot if act=='BUY' else (ep-xp)*lot; sl+=2*a.slippage*lot; tc+=charge(ep+a.slippage if act=='BUY' else max(0,ep-a.slippage),act,lot,d)+charge(max(0,xp-a.slippage) if act=='BUY' else xp+a.slippage,'SELL' if act=='BUY' else 'BUY',lot,d)
  if ok:rows.append({'day':str(d),'state':r.state,'horizon':r.horizon,'raw_gross':raw,'slippage_cost':sl,'transaction_costs':tc,'net_pnl':raw-sl-tc})
 con.close(); t=pd.DataFrame(rows); fr='base' if a.slippage==.20 else 'stress'; t.to_csv(out/f'trades_{fr}.csv',index=False); summarize(t).to_csv(out/f'true_cell_summary_{fr}.csv',index=False); print(json.dumps(gate))
if __name__=='__main__':main()
