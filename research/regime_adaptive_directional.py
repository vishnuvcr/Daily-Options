from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel


@dataclass(frozen=True)
class Config:
    family: str
    entry_start: int
    entry_end: int
    stop: float
    target: float
    hold: int
    vol_mult: float
    rsi_lo: float
    rsi_hi: float


LOT_FALLBACK = 65


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    down = -delta.clip(upper=0).ewm(alpha=1/period, adjust=False).mean()
    rs = up.div(down)
    out = 100 - 100 / (1 + rs)
    out = out.where(down != 0, np.where(up > 0, 100.0, 50.0))
    return out


def load(path: Path):
    spot = pd.read_excel(path, sheet_name="Spot_1min")
    opt = pd.read_excel(path, sheet_name="ATM_Options_1min")
    spot["timestamp"] = pd.to_datetime(spot["Date"].astype(str)+" "+spot["Time"].astype(str))
    opt["timestamp"] = pd.to_datetime(opt["Timestamp"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    spot = spot.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    opt = opt.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume","Type":"option_type","Strike":"strike","Expiry":"expiry"})
    opt["option_type"] = opt["option_type"].astype(str).str.upper().replace({"CALL":"CE","PUT":"PE","C":"CE","P":"PE"})
    for c in ["open","high","low","close","volume","strike"]:
        opt[c] = pd.to_numeric(opt[c], errors="coerce")
    return (
        spot.dropna(subset=["timestamp","close"]).sort_values("timestamp"),
        opt.dropna(subset=["timestamp","close","strike"]).sort_values("timestamp"),
    )


def features(day: pd.DataFrame) -> pd.DataFrame:
    x = day.sort_values("timestamp").copy()
    x["typical"] = (x.high+x.low+x.close)/3
    cumv = x.volume.clip(lower=0).cumsum().replace(0,np.nan)
    x["vwap"] = (x.typical*x.volume.clip(lower=0)).cumsum()/cumv
    x["ema8"] = x.close.ewm(span=8, adjust=False).mean()
    x["ema21"] = x.close.ewm(span=21, adjust=False).mean()
    x["ema50"] = x.close.ewm(span=50, adjust=False).mean()
    x["rsi"] = rsi(x.close)
    mid = x.close.rolling(20).mean()
    std = x.close.rolling(20).std()
    x["bb_u"] = mid + 2*std
    x["bb_l"] = mid - 2*std
    tr = pd.concat([
        x.high-x.low,
        (x.high-x.close.shift()).abs(),
        (x.low-x.close.shift()).abs(),
    ], axis=1).max(axis=1)
    x["atr"] = tr.rolling(14).mean()
    x["atr_pct"] = x.atr/x.close
    x["atr_regime"] = x.atr_pct.rolling(60, min_periods=20).rank(pct=True)
    x["vol_ratio"] = x.volume/x.volume.rolling(20,min_periods=10).mean().replace(0,np.nan)
    x["hh20"] = x.high.shift(1).rolling(20).max()
    x["ll20"] = x.low.shift(1).rolling(20).min()
    return x


def signal_at(x: pd.DataFrame, cfg: Config, day_date):
    start = pd.Timestamp(day_date) + pd.Timedelta(minutes=cfg.entry_start)
    end = pd.Timestamp(day_date) + pd.Timedelta(minutes=cfg.entry_end)
    z = x[(x.timestamp>=start)&(x.timestamp<=end)].copy()
    z = z.replace([np.inf,-np.inf],np.nan).dropna(subset=["close","vwap","ema21","ema50","rsi","atr_regime","vol_ratio"])
    if z.empty:
        return None

    if cfg.family == "trend":
        bull = (
            (z.close > z.vwap) &
            (z.ema21 > z.ema50) &
            (z.rsi.between(cfg.rsi_lo, cfg.rsi_hi)) &
            (z.vol_ratio >= cfg.vol_mult) &
            (z.close >= z.hh20) &
            (z.atr_regime >= 0.40)
        )
        bear = (
            (z.close < z.vwap) &
            (z.ema21 < z.ema50) &
            (z.rsi.between(100-cfg.rsi_hi, 100-cfg.rsi_lo)) &
            (z.vol_ratio >= cfg.vol_mult) &
            (z.close <= z.ll20) &
            (z.atr_regime >= 0.40)
        )
    elif cfg.family == "meanrev":
        bull = (
            (z.rsi <= cfg.rsi_lo) &
            (z.close <= z.bb_l) &
            (z.close < z.vwap) &
            (z.atr_regime <= 0.70)
        )
        bear = (
            (z.rsi >= cfg.rsi_hi) &
            (z.close >= z.bb_u) &
            (z.close > z.vwap) &
            (z.atr_regime <= 0.70)
        )
    else:
        raise ValueError(cfg.family)

    candidates=[]
    for _,r in z[bull].iterrows():
        candidates.append((r.timestamp,"CE"))
    for _,r in z[bear].iterrows():
        candidates.append((r.timestamp,"PE"))
    return min(candidates,key=lambda t:t[0]) if candidates else None


def backtest_day(ds, do, cfg, cm):
    d = ds.timestamp.dt.date.iloc[0]
    x = features(ds)
    sig = signal_at(x,cfg,d)
    if sig is None:
        return None

    st,typ = sig
    spot_px = float(ds[ds.timestamp>=st].iloc[0].close)
    q = do[(do.option_type==typ)&(do.timestamp>=st+pd.Timedelta(minutes=1))&(do.timestamp<=st+pd.Timedelta(minutes=4))&(do.close>0)].copy()
    if q.empty:
        return None
    strikes = q.strike.dropna().unique()
    strike = float(min(strikes,key=lambda s:abs(s-spot_px)))
    q = q[q.strike==strike].sort_values("timestamp")
    if q.empty:
        return None

    entry = float(q.iloc[0].close); et=q.iloc[0].timestamp
    path = do[(do.option_type==typ)&(do.strike==strike)&(do.timestamp>et)&(do.timestamp<=et+pd.Timedelta(minutes=cfg.hold))].sort_values("timestamp")
    if path.empty:
        return None

    stop_px = entry*(1-cfg.stop)
    tgt_px = entry*(1+cfg.target)
    exit_px=None; xt=None; reason="time"

    for _,r in path.iterrows():
        hit_s=float(r.low)<=stop_px
        hit_t=float(r.high)>=tgt_px
        if hit_s and hit_t:
            exit_px=stop_px; xt=r.timestamp; reason="stop_first"
            break
        if hit_s:
            exit_px=stop_px; xt=r.timestamp; reason="stop"
            break
        if hit_t:
            exit_px=tgt_px; xt=r.timestamp; reason="target"
            break
    if exit_px is None:
        rr=path.iloc[-1]
        exit_px=float(rr.close); xt=rr.timestamp

    lot=nifty_lot_size(d)
    net=cm.net_pnl(entry,exit_px,1,lot)
    return {
        "date":str(d),"entry_time":et.isoformat(),"exit_time":xt.isoformat(),
        "family":cfg.family,"option_type":typ,"strike":strike,"entry":entry,
        "exit":exit_px,"net_pnl":float(net),"reason":reason,"lot_size":lot,
        "signal_minute":int((et-pd.Timestamp(d)).total_seconds()/60),
    }


def build_trade_bases(spot, opt, configs):
    cm = OptionCostModel()
    spot_days={d:ds for d,ds in spot.groupby(spot.timestamp.dt.date)}
    opt_days={d:do for d,do in opt.groupby(opt.timestamp.dt.date)}
    bases=[]
    keys=sorted({(cfg.family,cfg.entry_start,cfg.vol_mult,cfg.rsi_lo,cfg.rsi_hi) for cfg in configs})

    for d,ds in spot_days.items():
        dsf=features(ds)
        do=opt_days.get(d)
        if do is None:
            continue
        for family,entry_start,vol_mult,rsi_lo,rsi_hi in keys:
            cfg=Config(family,entry_start,entry_start+75,0.20,0.40,60,vol_mult,rsi_lo,rsi_hi)
            sig=signal_at(dsf,cfg,d)
            if sig is None:
                continue
            st,typ=sig
            srow=ds[ds.timestamp>=st]
            if srow.empty:
                continue
            spot_px=float(srow.iloc[0].close)
            q=do[(do.option_type==typ)&(do.timestamp>=st+pd.Timedelta(minutes=1))&(do.timestamp<=st+pd.Timedelta(minutes=4))&(do.close>0)].copy()
            if q.empty:
                continue
            strike=float(min(q.strike.dropna().unique(),key=lambda s:abs(s-spot_px)))
            q=q[q.strike==strike].sort_values("timestamp")
            if q.empty:
                continue
            entry=float(q.iloc[0].close); et=q.iloc[0].timestamp
            path=do[(do.option_type==typ)&(do.strike==strike)&(do.timestamp>et)&(do.timestamp<=et+pd.Timedelta(minutes=90))].sort_values("timestamp")
            if path.empty:
                continue
            lot=nifty_lot_size(d)
            bases.append({
                "date":d,"family":family,"entry_start":entry_start,"vol_mult":vol_mult,
                "rsi_lo":rsi_lo,"rsi_hi":rsi_hi,"entry_time":et,"option_type":typ,
                "strike":strike,"entry":entry,"lot":lot,"path":path,
            })
    return bases, len(spot_days)


def precompute_outcomes(bases, configs, cm):
    out={}
    unique_risk=sorted({(cfg.stop,cfg.target,cfg.hold) for cfg in configs})
    for i,b in enumerate(bases):
        path=b["path"]
        for stop,target,hold in unique_risk:
            p=path[path.timestamp<=b["entry_time"]+pd.Timedelta(minutes=hold)]
            stop_px=b["entry"]*(1-stop)
            tgt_px=b["entry"]*(1+target)
            exit_px=None; reason="time"
            if not p.empty:
                for _,r in p.iterrows():
                    hit_s=float(r.low)<=stop_px
                    hit_t=float(r.high)>=tgt_px
                    if hit_s and hit_t:
                        exit_px=stop_px; reason="stop_first"; break
                    if hit_s:
                        exit_px=stop_px; reason="stop"; break
                    if hit_t:
                        exit_px=tgt_px; reason="target"; break
                if exit_px is None:
                    exit_px=float(p.iloc[-1].close)
            if exit_px is not None:
                out[(i,stop,target,hold)]=(
                    float(cm.net_pnl(b["entry"],exit_px,1,b["lot"])),
                    float(exit_px),reason
                )
    return out


def evaluate_bases(bases, all_days, configs, outcomes):
    results=[]
    for cfg in configs:
        daily={}
        trades=0
        for i,b in enumerate(bases):
            if (b["family"],b["entry_start"],b["vol_mult"],b["rsi_lo"],b["rsi_hi"]) != (
                cfg.family,cfg.entry_start,cfg.vol_mult,cfg.rsi_lo,cfg.rsi_hi
            ):
                continue
            key=(i,cfg.stop,cfg.target,cfg.hold)
            if key not in outcomes:
                continue
            net,exit_px,reason=outcomes[key]
            daily[b["date"]]=daily.get(b["date"],0.0)+net
            trades+=1
        if trades < max(60,int(0.45*all_days)):
            continue
        all_daily=pd.Series(0.0,index=pd.Index(sorted({b["date"] for b in bases})))
        if daily:
            for d,v in daily.items(): all_daily.loc[d]=v
        eq=all_daily.cumsum(); dd=eq-eq.cummax()
        wins=all_daily[all_daily>0].sum(); losses=-all_daily[all_daily<0].sum()
        results.append({
            "family":cfg.family,"entry_start":cfg.entry_start,"entry_end":cfg.entry_end,
            "stop":cfg.stop,"target":cfg.target,"hold":cfg.hold,"vol_mult":cfg.vol_mult,
            "rsi_lo":cfg.rsi_lo,"rsi_hi":cfg.rsi_hi,"trades":trades,
            "coverage":trades/all_days,"mean_day_net":float(all_daily.mean()),
            "median_day_net":float(all_daily.median()),"p10_day_net":float(all_daily.quantile(0.10)),
            "positive_day_rate":float((all_daily>0).mean()),"win_rate_trade":float((all_daily.loc[all_daily!=0]>0).mean()) if (all_daily!=0).any() else 0.0,
            "profit_factor":float(wins/losses) if losses else 999.0,"max_drawdown":float(dd.min())
        })
    board=pd.DataFrame(results)
    if not board.empty:
        board=board.sort_values(["mean_day_net","positive_day_rate","profit_factor"],ascending=[False,False,False])
    return board


def main(data,out):
    spot,opt=load(data)
    configs=[]
    for family in ("trend","meanrev"):
        for entry_start in (9*60+30,9*60+45,10*60,10*60+15):
            for stop in (0.15,0.20,0.25,0.30):
                for target in (0.30,0.40,0.50,0.60):
                    for hold in (30,60,90):
                        for vol_mult in (1.0,1.2,1.5):
                            rsi_lo,rsi_hi=(55,70) if family=="trend" else (30,70)
                            configs.append(Config(
                                family,entry_start,entry_start+75,stop,target,hold,
                                vol_mult,rsi_lo,rsi_hi
                            ))
    cm=OptionCostModel()
    bases,all_days=build_trade_bases(spot,opt,configs)
    outcomes=precompute_outcomes(bases,configs,cm)
    board=evaluate_bases(bases,all_days,configs,outcomes)
    out.mkdir(parents=True,exist_ok=True)
    board.head(250).to_csv(out/"regime_adaptive_leaderboard.csv",index=False)
    qualified=board[board.mean_day_net>=1000] if not board.empty else pd.DataFrame()
    summary={
        "calendar_days":int(spot.timestamp.dt.date.nunique()),
        "trade_bases":len(bases),
        "variants_tested":len(configs),
        "target_daily_net_inr":1000.0,
        "target_qualified_count":int(len(qualified)),
        "best":board.iloc[0].to_dict() if not board.empty else None,
    }
    (out/"regime_adaptive_summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))


if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("reports")); a=ap.parse_args(); main(a.data,a.out)
