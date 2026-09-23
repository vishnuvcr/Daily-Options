from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel

ANNUAL_MINUTES = 252 * 375
RISK_FREE = 0.06


@dataclass(frozen=True)
class Config:
    entry_minutes: int
    stop_mult: float
    target_decay: float
    hold_minutes: int
    gap_max: float | None
    first15_range_max: float | None
    vrp_min: float | None


def load(path: Path):
    spot = pd.read_excel(path, sheet_name="Spot_1min")
    opt = pd.read_excel(path, sheet_name="ATM_Options_1min")
    spot["timestamp"] = pd.to_datetime(spot["Date"].astype(str) + " " + spot["Time"].astype(str))
    opt["timestamp"] = pd.to_datetime(opt["Timestamp"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    spot = spot.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    opt = opt.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume","Type":"option_type","Strike":"strike","Expiry":"expiry"})
    opt["option_type"] = opt["option_type"].astype(str).str.upper().replace({"CALL":"CE","PUT":"PE"})
    opt["expiry"] = pd.to_datetime(opt["expiry"], errors="coerce")
    for c in ["open","high","low","close","volume","strike"]:
        opt[c] = pd.to_numeric(opt[c], errors="coerce")
    return (
        spot.dropna(subset=["timestamp","close"]).sort_values("timestamp"),
        opt.dropna(subset=["timestamp","close","strike","expiry"]).sort_values("timestamp"),
    )


def implied_vol_from_straddle(s: float, k: float, years: float, premium: float) -> float:
    if s <= 0 or k <= 0 or premium <= 0 or years <= 0:
        return np.nan

    def cdf(x):
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    def call(sig):
        if sig <= 0:
            return max(s - k * math.exp(-RISK_FREE * years), 0.0)
        d1 = (math.log(s/k) + (RISK_FREE + 0.5*sig*sig)*years) / (sig*math.sqrt(years))
        d2 = d1 - sig*math.sqrt(years)
        return s*cdf(d1) - k*math.exp(-RISK_FREE*years)*cdf(d2)

    intrinsic = abs(s-k)
    if premium <= intrinsic:
        return np.nan

    lo, hi = 1e-4, 5.0
    for _ in range(50):
        mid = (lo + hi) / 2
        model = call(mid) + (call(mid) - s + k*math.exp(-RISK_FREE*years))
        if model > premium:
            hi = mid
        else:
            lo = mid
    return (lo+hi)/2


def build_observations(spot, opt):
    spot_days = {d: ds.copy() for d, ds in spot.groupby(spot.timestamp.dt.date)}
    opt_days = {d: do.copy() for d, do in opt.groupby(opt.timestamp.dt.date)}
    observations = []

    for d, ds in spot_days.items():
        do = opt_days.get(d)
        if do is None:
            continue

        ds = ds.sort_values("timestamp").copy()
        do = do.sort_values("timestamp").copy()
        prev = spot[spot.timestamp.dt.date < d].sort_values("timestamp")
        prev_close = float(prev.close.iloc[-1]) if not prev.empty else np.nan

        first15 = ds[(ds.timestamp >= pd.Timestamp(d)+pd.Timedelta(hours=9, minutes=15)) & (ds.timestamp < pd.Timestamp(d)+pd.Timedelta(hours=9, minutes=30))]
        first15_high = float(first15.high.max()) if not first15.empty else np.nan
        first15_low = float(first15.low.min()) if not first15.empty else np.nan

        for entry_minutes in (15,30,45,60,75,90,105):
            entry_time = pd.Timestamp(d) + pd.Timedelta(hours=9, minutes=15+entry_minutes)
            q = do[(do.timestamp >= entry_time) & (do.timestamp <= entry_time + pd.Timedelta(minutes=3)) & (do.close > 0)]
            if q.empty:
                continue

            srow = ds[ds.timestamp <= entry_time].tail(1)
            if srow.empty:
                continue
            spot_px = float(srow.close.iloc[0])
            strikes = q.strike.dropna().unique()
            if len(strikes) == 0:
                continue
            strike = float(min(strikes, key=lambda x: abs(x-spot_px)))

            ce = q[(q.option_type=="CE") & (q.strike==strike)].sort_values("timestamp")
            pe = q[(q.option_type=="PE") & (q.strike==strike)].sort_values("timestamp")
            common = sorted(set(ce.timestamp) & set(pe.timestamp))
            if not common:
                continue
            et = common[0]
            ce0 = float(ce.loc[ce.timestamp==et, "close"].iloc[0])
            pe0 = float(pe.loc[pe.timestamp==et, "close"].iloc[0])
            entry = ce0 + pe0
            if entry <= 0:
                continue

            hist = ds[(ds.timestamp < et) & (ds.timestamp >= et-pd.Timedelta(minutes=30))].close
            rv = float(hist.pct_change().dropna().std()*math.sqrt(ANNUAL_MINUTES)) if len(hist) >= 15 else np.nan

            expiry = pd.Timestamp(ce.iloc[0].expiry)
            years = max((expiry-et)/pd.Timedelta(days=365.25), 1/3650)
            iv = implied_vol_from_straddle(spot_px, strike, float(years), entry)
            vrp = iv-rv if np.isfinite(iv) and np.isfinite(rv) else np.nan

            gap = abs((float(ds.open.iloc[0])-prev_close)/prev_close) if np.isfinite(prev_close) and prev_close else np.nan
            first15_range = ((first15_high-first15_low)/spot_px) if np.isfinite(first15_high) and np.isfinite(first15_low) and spot_px else np.nan

            path = do[(do.timestamp>et) & (do.timestamp<=et+pd.Timedelta(minutes=240)) & (do.strike==strike)]
            piv = path.pivot_table(index="timestamp", columns="option_type", values=["high","low","close"], aggfunc="last")
            if piv.empty or not {"CE","PE"}.issubset(set(piv["close"].columns)):
                continue
            piv = piv.dropna(subset=[("close","CE"),("close","PE")])
            if piv.empty:
                continue

            observations.append({
                "date": d, "entry_minutes": entry_minutes, "entry": entry,
                "gap": gap, "first15_range": first15_range, "vrp": vrp,
                "piv": piv, "lot": nifty_lot_size(d),
            })
    return observations, len(spot_days)


def net_short_straddle(entry: float, exit_straddle: float, lot: int, cm: OptionCostModel) -> float:
    gross = (entry-exit_straddle)*lot
    turnover = (entry+exit_straddle)*lot
    brokerage = 4.0*cm.brokerage_per_order
    exchange = turnover*cm.exchange_rate
    sebi = turnover*cm.sebi_rate
    stt = entry*lot*cm.stt_sell_rate
    stamp = exit_straddle*lot*cm.stamp_buy_rate
    gst = cm.gst_rate*(brokerage+exchange+sebi)
    slippage = 4.0*0.20*lot
    return float(gross-(brokerage+exchange+sebi+stt+stamp+gst+slippage))


def precompute_base_outcomes(observations, base_configs):
    cm = OptionCostModel()
    unique_core = sorted({
        (c.entry_minutes,c.stop_mult,c.target_decay,c.hold_minutes)
        for c in base_configs
    })
    outcomes = {}
    for idx, row in enumerate(observations):
        piv = row["piv"]
        hi = (piv[("high","CE")].to_numpy(dtype=float) + piv[("high","PE")].to_numpy(dtype=float))
        lo = (piv[("low","CE")].to_numpy(dtype=float) + piv[("low","PE")].to_numpy(dtype=float))
        close = (piv[("close","CE")].to_numpy(dtype=float) + piv[("close","PE")].to_numpy(dtype=float))
        ts = piv.index.to_numpy()
        for entry_minutes, stop_mult, target_decay, hold_minutes in unique_core:
            if entry_minutes != row["entry_minutes"]:
                continue
            n = min(len(close), int(hold_minutes))
            if n <= 0:
                continue
            stop = row["entry"]*stop_mult
            target = row["entry"]*(1-target_decay)
            sh = np.flatnonzero(hi[:n] >= stop)
            th = np.flatnonzero(lo[:n] <= target)
            stop_idx = int(sh[0]) if len(sh) else None
            target_idx = int(th[0]) if len(th) else None

            if stop_idx is None and target_idx is None:
                exit_idx = n-1
                exit_price = close[exit_idx]
                reason = "time"
            elif stop_idx is None:
                exit_idx = target_idx
                exit_price = target
                reason = "target"
            elif target_idx is None:
                exit_idx = stop_idx
                exit_price = stop
                reason = "stop"
            elif stop_idx <= target_idx:
                exit_idx = stop_idx
                exit_price = stop
                reason = "stop_first"
            else:
                exit_idx = target_idx
                exit_price = target
                reason = "target"

            outcomes[(idx,entry_minutes,stop_mult,target_decay,hold_minutes)] = (
                net_short_straddle(row["entry"], float(exit_price), row["lot"], cm),
                str(ts[exit_idx]),
                reason,
                float(exit_price),
            )
    return outcomes


def evaluate_core(observations, all_days, configs, outcomes):
    results=[]
    for cfg in configs:
        pnl_by_date={}
        records=0
        for idx,row in enumerate(observations):
            if row["entry_minutes"] != cfg.entry_minutes:
                continue
            key=(idx,cfg.entry_minutes,cfg.stop_mult,cfg.target_decay,cfg.hold_minutes)
            if key not in outcomes:
                continue
            net,exit_ts,reason,exit_price=outcomes[key]
            pnl_by_date[row["date"]] = pnl_by_date.get(row["date"],0.0)+net
            records += 1
        daily = pd.Series(0.0,index=pd.Index(sorted(set(o["date"] for o in observations))))
        for d,v in pnl_by_date.items():
            daily.loc[d]=v
        if records < max(60,int(0.5*all_days)):
            continue
        eq=daily.cumsum(); dd=eq-eq.cummax()
        wins=daily[daily>0].sum(); losses=-daily[daily<0].sum()
        results.append({
            "entry_minutes":cfg.entry_minutes,"stop_mult":cfg.stop_mult,"target_decay":cfg.target_decay,
            "hold_minutes":cfg.hold_minutes,"trades":records,"coverage":records/all_days,
            "mean_day_net":float(daily.mean()),"median_day_net":float(daily.median()),
            "p10_day_net":float(daily.quantile(0.10)),"positive_day_rate":float((daily>0).mean()),
            "max_drawdown":float(dd.min()),"profit_factor":float(wins/losses) if losses>0 else 999.0
        })
    return pd.DataFrame(results)


def evaluate_filtered(observations, all_days, top_core, outcomes):
    results=[]
    for _,base in top_core.iterrows():
        for gap in (0.003,0.005,0.008):
            for r15 in (0.002,0.003,0.004,0.005):
                for vrp in (None,0.00,0.02,0.04,0.06):
                    pnl_by_date={}
                    records=0
                    for idx,row in enumerate(observations):
                        if row["entry_minutes"] != int(base.entry_minutes):
                            continue
                        if gap is not None and (not np.isfinite(row["gap"]) or row["gap"]>gap):
                            continue
                        if r15 is not None and (not np.isfinite(row["first15_range"]) or row["first15_range"]>r15):
                            continue
                        if vrp is not None and (not np.isfinite(row["vrp"]) or row["vrp"]<vrp):
                            continue

                        key=(idx,int(base.entry_minutes),float(base.stop_mult),float(base.target_decay),int(base.hold_minutes))
                        if key not in outcomes:
                            continue
                        net,_,_,_=outcomes[key]
                        pnl_by_date[row["date"]] = pnl_by_date.get(row["date"],0.0)+net
                        records+=1

                    daily=pd.Series(0.0,index=pd.Index(sorted(set(o["date"] for o in observations))))
                    for d,v in pnl_by_date.items():
                        daily.loc[d]=v
                    if records < max(80,int(0.60*all_days)):
                        continue
                    eq=daily.cumsum(); dd=eq-eq.cummax()
                    wins=daily[daily>0].sum(); losses=-daily[daily<0].sum()
                    results.append({
                        "entry_minutes":int(base.entry_minutes),"stop_mult":float(base.stop_mult),
                        "target_decay":float(base.target_decay),"hold_minutes":int(base.hold_minutes),
                        "gap_max":gap,"first15_range_max":r15,"vrp_min":vrp,"trades":records,
                        "coverage":records/all_days,"mean_day_net":float(daily.mean()),
                        "median_day_net":float(daily.median()),"p10_day_net":float(daily.quantile(0.10)),
                        "positive_day_rate":float((daily>0).mean()),"max_drawdown":float(dd.min()),
                        "profit_factor":float(wins/losses) if losses>0 else 999.0
                    })
    return pd.DataFrame(results)


def main(data: Path, out: Path):
    spot,opt=load(data)
    observations,all_days=build_observations(spot,opt)
    base=[Config(e,s,t,h,None,None,None) for e in (15,30,45,60,75,90,105) for s in (1.4,1.6,1.8,2.0) for t in (0.25,0.35,0.45,0.55,0.65) for h in (60,120,180)]
    outcomes=precompute_base_outcomes(observations,base)
    core=evaluate_core(observations,all_days,base,outcomes)
    core=core.sort_values(["mean_day_net","positive_day_rate","max_drawdown"],ascending=[False,False,False]) if not core.empty else core
    top=core.head(20) if not core.empty else core
    filtered=evaluate_filtered(observations,all_days,top,outcomes) if not top.empty else pd.DataFrame()
    if not filtered.empty:
        filtered=filtered.sort_values(["mean_day_net","positive_day_rate","max_drawdown"],ascending=[False,False,False])
    out.mkdir(parents=True,exist_ok=True)
    core.to_csv(out/"straddle_grid_base.csv",index=False)
    filtered.head(250).to_csv(out/"straddle_grid_filtered.csv",index=False)
    promoted=filtered[filtered.mean_day_net>=1000] if not filtered.empty else pd.DataFrame()
    summary={
        "dataset":str(data),"calendar_days":all_days,"entry_observations":len(observations),
        "base_variants_tested":len(base),"filtered_variants_tested":len(top)*3*4*5,
        "target_daily_net_inr":1000.0,"target_qualified_count":int(len(promoted)),
        "best_mean_day":float(filtered.iloc[0].mean_day_net) if not filtered.empty else (float(core.iloc[0].mean_day_net) if not core.empty else None),
        "best_positive_day_rate":float(filtered.iloc[0].positive_day_rate) if not filtered.empty else (float(core.iloc[0].positive_day_rate) if not core.empty else None),
        "best_max_drawdown":float(filtered.iloc[0].max_drawdown) if not filtered.empty else (float(core.iloc[0].max_drawdown) if not core.empty else None),
        "best":filtered.iloc[0].to_dict() if not filtered.empty else (core.iloc[0].to_dict() if not core.empty else None),
    }
    (out/"straddle_grid_summary.json").write_text(json.dumps(summary,indent=2,default=str),encoding="utf-8")
    print(json.dumps(summary,indent=2,default=str))


if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("reports")); args=ap.parse_args()
    main(args.data,args.out)
