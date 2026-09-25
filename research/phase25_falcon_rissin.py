from pathlib import Path
import argparse,json
from datetime import date
import duckdb,numpy as np,pandas as pd

ENTRY_TIMES=("09:30:00","10:00:00","11:00:00","13:00:00","14:00:00")
TARGET_PREMIUMS=(20.,25.,30.); FAR_MODES=("DIAGONAL_PREMIUM","SAME_STRIKE")
ADJUST_TIMES=("09:30:00","10:00:00","11:00:00"); STOP_MULTIPLES=(.5,1.,1.5)
START_DATE="2024-10-01"; END_DATE="2025-12-31"
RISSIN_REVISION="78b1c5468255d18cf492984bfe6fe4e3ac874d7c"
_CHAIN_CACHE={}
_SERIES_CACHE={}

def variant_grid():
    return [(e,p,f,a,s) for e in ENTRY_TIMES for p in TARGET_PREMIUMS for f in FAR_MODES for a in ADJUST_TIMES for s in STOP_MULTIPLES]
def expiry_offsets(): return (-4,-3,-1)
def vid(v): return f"{v[0]}|p{v[1]:g}|{v[2]}|adj{v[3]}|stop{v[4]:g}"
def lot_size(e):
    d=pd.Timestamp(e).date()
    return 50 if d<pd.Timestamp("2024-04-26").date() else 25 if d<pd.Timestamp("2024-11-21").date() else 75 if d<pd.Timestamp("2026-01-06").date() else 65

def src(root):
    ps=[root/"upstox_intraday/NIFTY/NIFTY_2024.parquet",root/"upstox_intraday/NIFTY/NIFTY_2025.parquet"]
    if any(not p.exists() for p in ps): raise FileNotFoundError("missing pinned Rissin NIFTY files")
    return "read_parquet([" + ",".join("'" + str(p).replace("'","''") + "'" for p in ps) + "])"

def target(df,side,p,ref=None,outward=False):
    x=df[df["option_type"]==side].copy()
    if ref is not None: x=x[x["strike"]>=ref] if side=="CE" and outward else x[x["strike"]<=ref] if side=="PE" and outward else x[x["strike"]==ref]
    x=x[(x["open_px"]>0)&(x["close_px"]>0)]
    if x.empty:return None
    x["d"]=(x["close_px"]-p).abs(); return x.sort_values(["d","strike"]).iloc[0]

def chain(c,S,e,d,a,b):
    key=(S,e,d,str(a),str(b))
    if key in _CHAIN_CACHE:
        return _CHAIN_CACHE[key]
    q=f"""SELECT CAST(timestamp AS TIMESTAMP) ts,CAST(strike AS DOUBLE) strike,UPPER(CAST(option_type AS VARCHAR)) option_type,CAST(open AS DOUBLE) open_px,CAST(close AS DOUBLE) close_px FROM {S}
    WHERE CAST(date AS DATE)=DATE '{d}' AND CAST(expiry AS DATE)=DATE '{e}' AND CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{a}' AND TIMESTAMP '{b}' AND granularity='1min' AND close>0 ORDER BY ts,strike"""
    out=c.execute(q).df()
    _CHAIN_CACHE[key]=out
    return out

def series(c,S,d,e,k,side,a,b):
    key=(S,d,e,float(k),side,str(a),str(b))
    if key in _SERIES_CACHE:
        return _SERIES_CACHE[key]
    start_day=pd.Timestamp(a).date()
    end_day=pd.Timestamp(b).date()
    q=f"""SELECT CAST(timestamp AS TIMESTAMP) ts,CAST(open AS DOUBLE) open_px,CAST(close AS DOUBLE) close_px FROM {S}
    WHERE CAST(date AS DATE) BETWEEN DATE '{start_day}' AND DATE '{end_day}' AND CAST(expiry AS DATE)=DATE '{e}' AND CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{a}' AND TIMESTAMP '{b}'
    AND CAST(strike AS DOUBLE)={float(k)} AND UPPER(CAST(option_type AS VARCHAR))='{side}' AND granularity='1min' AND close>0 ORDER BY ts"""
    x=c.execute(q).df()
    if x.empty:
        out=pd.DataFrame(columns=["ts","open_px","close_px"])
        _SERIES_CACHE[key]=out
        return out
    x.ts=pd.to_datetime(x.ts).dt.floor("min")
    out=x.drop_duplicates("ts")
    _SERIES_CACHE[key]=out
    return out
def op(df,side,k,t):
    x=df[(df.option_type==side)&(df.strike==float(k))&(df.ts==pd.Timestamp(t))]
    return None if x.empty or x.iloc[0].open_px<=0 else float(x.iloc[0].open_px)
def nxt(x,t):
    z=x[x.ts>=pd.Timestamp(t)]; return None if z.empty else z.iloc[0]
def panel(m):
    b=None
    for n,s in m.items():
        z=s[["ts","close_px"]].rename(columns={"close_px":n}).sort_values("ts")
        b=z if b is None else pd.merge_asof(b,z,on="ts",direction="backward",tolerance=pd.Timedelta("1min"))
    return b.dropna().sort_values("ts") if b is not None else pd.DataFrame()

def setup(c,S,d,et,p,f,exps,sessions):
    fut=[e for e in exps if e>=d]
    if len(fut)<2:return None
    ne,fe=fut[:2]; prior=[x for x in sessions if x<ne]
    if len(prior)<4 or prior[-4]!=d:return None
    ad,xd=prior[-3],prior[-1]; t=pd.Timestamp(f"{d} {et}"); ft=t+pd.Timedelta("1min")
    n=chain(c,S,ne,d,t,ft); z=chain(c,S,fe,d,t,ft)
    if n.empty or z.empty:return None
    nc,nf=n[n.ts==t],n[n.ts==ft]; fc,ff=z[z.ts==t],z[z.ts==ft]
    ce,pe=target(nc,"CE",p),target(nc,"PE",p)
    if ce is None or pe is None:return None
    if f=="SAME_STRIKE": fce,fpe=target(fc,"CE",p,float(ce["strike"])),target(fc,"PE",p,float(pe["strike"]))
    else: fce,fpe=target(fc,"CE",p,float(ce["strike"]),True),target(fc,"PE",p,float(pe["strike"]),True)
    vals=None if fce is None or fpe is None else [op(nf,"CE",float(ce["strike"]),ft),op(nf,"PE",float(pe["strike"]),ft),op(ff,"CE",float(fce["strike"]),ft),op(ff,"PE",float(fpe["strike"]),ft)]
    if not vals or any(x is None for x in vals):return None
    a,b,cc,d0=vals; credit=5*(a+b)-3*(cc+d0)
    return None if credit<=0 else {"d":d,"et":et,"p":p,"f":f,"ne":ne,"fe":fe,"ad":ad,"xd":xd,"fill":ft,"credit":credit,
        "sce":float(ce["strike"]),"spe":float(pe["strike"]),"fce":float(fce["strike"]),"fpe":float(fpe["strike"]),"sce0":a,"spe0":b,"fce0":cc,"fpe0":d0}

def costs(legs,lot,slip,ed,xd):
    turnover=sum((x[0]+x[1])*x[2]*lot for x in legs)
    se=sum(x[0]*x[2]*lot for x in legs if x[3]<0); sx=sum(x[1]*x[2]*lot for x in legs if x[3]>0)
    be=sum(x[0]*x[2]*lot for x in legs if x[3]>0); bx=sum(x[1]*x[2]*lot for x in legs if x[3]<0)
    bro=40*len(legs); ex=turnover*(.0003503 if pd.Timestamp(ed).date()<date(2026,3,1) else .000355299); sebi=turnover*.000001
    stt=se*(.001 if pd.Timestamp(ed).date()<date(2026,4,1) else .0015)+sx*(.001 if pd.Timestamp(xd).date()<date(2026,4,1) else .0015)
    return bro+ex+sebi+stt+(be+bx)*.00003+.18*(bro+ex+sebi)+2*slip*sum(x[2]*lot for x in legs)

def sim(c,S,s,v,slip):
    d,ne,fe,ad,xd=s["d"],s["ne"],s["fe"],s["ad"],s["xd"]; lot=lot_size(ne); start=s["fill"]; end=pd.Timestamp(f"{xd} 15:15")
    I={k:series(c,S,d,ne,s[k],side,start,end) for k,side in [("sce","CE"),("spe","PE")]}
    I.update(fce=series(c,S,d,fe,s["fce"],"CE",start,end),fpe=series(c,S,d,fe,s["fpe"],"PE",start,end))
    if any(x.empty for x in I.values()):return None
    q=f"SELECT DISTINCT CAST(strike AS DOUBLE) strike,UPPER(CAST(option_type AS VARCHAR)) option_type FROM {S} WHERE CAST(date AS DATE)=DATE '{ad}' AND CAST(expiry AS DATE)=DATE '{ne}' AND granularity='1min'"
    st=c.execute(q).df(); ce=np.sort(st.loc[st.option_type=="CE","strike"].unique()); pe=np.sort(st.loc[st.option_type=="PE","strike"].unique())
    cw=ce[ce>s["sce"]]; pw=pe[pe<s["spe"]]
    if len(cw)==0 or len(pw)==0:return None
    wc,wp=float(cw[0]),float(pw[-1]); sig=pd.Timestamp(f"{ad} {v[3]}"); ex=sig+pd.Timedelta("1min")
    pre=panel(I); stop=None
    for r in pre.itertuples():
        if r.ts>=sig:break
        p=s["credit"]-5*r.sce-5*r.spe+3*r.fce+3*r.fpe
        if p<=-v[4]*s["credit"]:stop=r.ts;break
    base=[(s["sce0"],None,5,-1,"sce"),(s["spe0"],None,5,-1,"spe"),(s["fce0"],None,3,1,"fce"),(s["fpe0"],None,3,1,"fpe")]
    if stop is not None:
        out=[]
        for a,b,qy,sg,n in base:
            z=nxt(I[n],stop+pd.Timedelta("1min"))
            if z is None:return None
            out.append((a,float(z.open_px),qy,sg,n))
        gross=sum(sg*(b-a)*qy*lot for a,b,qy,sg,n in out)
        return {"reason":"STOP_PRE_ADJUST","exit":stop+pd.Timedelta("1min"),"pnl":gross-costs(out,lot,slip,d,(stop+pd.Timedelta("1min")).date())}
    Wc=series(c,S,ad,ne,wc,"CE",ex,end); Wp=series(c,S,ad,ne,wp,"PE",ex,end)
    ec,ep=nxt(Wc,ex),nxt(Wp,ex)
    if ec is None or ep is None:return None
    post=panel({"sce":I["sce"],"spe":I["spe"],"fce":I["fce"],"fpe":I["fpe"],"wc":Wc,"wp":Wp}); stop=None
    for r in post.itertuples():
        p=s["credit"]-5*r.sce-5*r.spe+3*r.fce+3*r.fpe+5*r.wc+5*r.wp-5*ec.open_px-5*ep.open_px
        if p<=-v[4]*s["credit"]:stop=r.ts;break
    legs=base+[(float(ec.open_px),None,5,1,"wc"),(float(ep.open_px),None,5,1,"wp")]; xs=stop if stop is not None else end
    out=[]
    for a,b,qy,sg,n in legs:
        z=nxt(Wc if n=="wc" else Wp if n=="wp" else I[n],xs+pd.Timedelta("1min"))
        if z is None:
            zz=(Wc if n=="wc" else Wp if n=="wp" else I[n]); zz=zz[zz.ts<=xs].tail(1)
            if zz.empty:return None
            px=float(zz.iloc[0].close_px)
        else:px=float(z.open_px)
        out.append((a,px,qy,sg,n))
    gross=sum(sg*(b-a)*qy*lot for a,b,qy,sg,n in out)
    return {"reason":"STOP_POST_ADJUST" if stop is not None else "PRE_EXPIRY_EXIT","exit":xs,"pnl":gross-costs(out,lot,slip,d,xs.date())}

def run(data,out,slip):
    _CHAIN_CACHE.clear(); _SERIES_CACHE.clear()
    out.mkdir(parents=True,exist_ok=True); S=src(data); c=duckdb.connect(); c.execute("SET TimeZone='Asia/Kolkata'")
    days=[pd.Timestamp(x).date() for x in c.execute(f"SELECT DISTINCT CAST(date AS DATE) d FROM {S} WHERE CAST(date AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}' AND granularity='1min' ORDER BY d").df().d]
    exps=[pd.Timestamp(x).date() for x in c.execute(f"SELECT DISTINCT CAST(expiry AS DATE) e FROM {S} WHERE CAST(date AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}' AND granularity='1min' ORDER BY e").df().e]
    if len(days)<200 or len(exps)<40:raise RuntimeError(f"coverage gate failed: {len(days)} days, {len(exps)} expiries")
    setups=[]
    for d in days:
        for et in ENTRY_TIMES:
            for p in TARGET_PREMIUMS:
                for f in FAR_MODES:
                    x=setup(c,S,d,et,p,f,exps,days)
                    if x:setups.append(x)
    nd=len({x["d"] for x in setups})
    if nd<20:raise RuntimeError(f"setup coverage gate failed: {nd} entry dates")
    rows=[]
    variants_by_setup={}
    for v in variant_grid():
        variants_by_setup.setdefault(v[:3],[]).append(v)
    for s in setups:
        for v in variants_by_setup[(s["et"],s["p"],s["f"])]:
            try:r=sim(c,S,s,v,slip)
            except Exception as e:r=None
            if r:rows.append({"variant_id":vid(v),"trade_date":s["d"],"net_pnl":r["pnl"],"reason":r["reason"],"exit_ts":r["exit"],"near_expiry":s["ne"],"far_expiry":s["fe"]})
    c.close(); tr=pd.DataFrame(rows)
    if tr.empty: raise RuntimeError("no executable trades after setup coverage gate")
    tr.to_csv(out/"phase25_trades.csv",index=False)
    d=tr.groupby(["variant_id","trade_date"],as_index=False).net_pnl.sum()
    b=tr.groupby("variant_id").agg(trades=("net_pnl","size"),total_net=("net_pnl","sum"),win_rate=("net_pnl",lambda x:float((x>0).mean()))).reset_index()
    st=d.groupby("variant_id").net_pnl.agg(["mean","median"]).reset_index().rename(columns={"mean":"mean_active_day_net","median":"median_active_day_net"})
    b=b.merge(st,on="variant_id");b["target_qualified"]=b.mean_active_day_net>=1000;b=b.sort_values("mean_active_day_net",ascending=False);b.to_csv(out/"phase25_leaderboard.csv",index=False)
    sm={"variants":270,"setups":len(setups),"setup_entry_dates":nd,"trades":len(tr),"positive_variants":int((b.mean_active_day_net>0).sum()),"target_qualified":int(b.target_qualified.sum()),"best":b.iloc[0].to_dict(),"slippage":slip}
    (out/"phase25_summary.json").write_text(json.dumps(sm,indent=2,default=str));return sm

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--data",type=Path,required=True);a.add_argument("--out",type=Path,required=True);a.add_argument("--slippage",type=float,default=.2);x=a.parse_args();print(json.dumps(run(x.data,x.out,x.slippage),indent=2,default=str))
