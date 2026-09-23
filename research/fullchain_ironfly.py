from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel


@dataclass(frozen=True)
class Core:
    entry: str
    wing_step: int
    stop_mult: float
    target_decay: float
    hold: int


def load(path: Path) -> pl.DataFrame:
    cols=["date","timestamp","expiry","strike","option_type","high","low","close"]
    table=pq.read_table(path,columns=cols)
    ts_idx=table.schema.get_field_index("timestamp")
    ts_type=table.schema.field("timestamp").type
    if pa.types.is_timestamp(ts_type) and ts_type.tz:
        naive=pc.cast(table["timestamp"],pa.timestamp("us"))
        table=table.set_column(ts_idx,"timestamp",naive)
    df=pl.from_arrow(table)
    return (
        df.with_columns([
            pl.col("date").cast(pl.Date),
            pl.col("timestamp").cast(pl.Datetime("us")),
            pl.col("expiry").cast(pl.Date),
            pl.col("strike").cast(pl.Float64),
            pl.col("option_type").cast(pl.String).str.to_uppercase(),
            pl.col("high").cast(pl.Float64),
            pl.col("low").cast(pl.Float64),
            pl.col("close").cast(pl.Float64),
        ])
        .filter(pl.col("option_type").is_in(["CE","PE"]))
    )


def net_credit_pnl(entry_credit, exit_value, lot, cm: OptionCostModel,
                   sc_entry, sp_entry, lc_entry, lp_entry,
                   sc_exit, sp_exit, lc_exit, lp_exit):
    gross=(entry_credit-exit_value)*lot
    turnover=(sc_entry+sp_entry+lc_entry+lp_entry+sc_exit+sp_exit+lc_exit+lp_exit)*lot
    brokerage=8*cm.brokerage_per_order
    exchange=turnover*cm.exchange_rate
    sebi=turnover*cm.sebi_rate
    # STT on option sales only: short legs opened + long wings closed.
    stt=(sc_entry+sp_entry+lc_exit+lp_exit)*lot*cm.stt_sell_rate
    stamp=(lc_entry+lp_entry+sc_exit+sp_exit)*lot*cm.stamp_buy_rate
    gst=cm.gst_rate*(brokerage+exchange+sebi)
    slippage=8*0.20*lot
    return float(gross-(brokerage+exchange+sebi+stt+stamp+gst+slippage))


def prepare_observations(df: pl.DataFrame):
    observations=[]
    partitions=df.partition_by("date",maintain_order=True,as_dict=True)
    dates=sorted(partitions.keys())

    for day in dates:
        daydf=partitions[day].filter(
            (pl.col("timestamp")>=pd.Timestamp(day).to_datetime64()+np.timedelta64(9*60+15,"m")) &
            (pl.col("timestamp")<=pd.Timestamp(day).to_datetime64()+np.timedelta64(13*60+15,"m"))
        )
        expiries=daydf.select(pl.col("expiry").unique().sort()).to_series().to_list()
        expiries=[e for e in expiries if e is not None and e>=day]
        if not expiries:
            continue
        expiry=expiries[0]
        expiry_df=daydf.filter(pl.col("expiry")==expiry)
        strikes=sorted(expiry_df.select(pl.col("strike").unique()).to_series().to_list())
        if len(strikes)<5:
            continue

        for entry_label in ("09:30:00","09:45:00","10:00:00"):
            et=pd.Timestamp(f"{day} {entry_label}")
            q=expiry_df.filter(
                (pl.col("timestamp")>=et.to_datetime64()) &
                (pl.col("timestamp")<=(et+pd.Timedelta(minutes=2)).to_datetime64()) &
                (pl.col("close")>0)
            )
            if q.height==0:
                continue

            px=(q.select(["strike","option_type","close"])
                .group_by(["strike","option_type"]).agg(pl.col("close").first())
                .pivot(values="close",index="strike",columns="option_type",aggregate_function="first"))
            if "CE" not in px.columns or "PE" not in px.columns:
                continue
            px=px.drop_nulls(["CE","PE"]).with_columns((pl.col("CE")-pl.col("PE")).abs().alias("gap")).sort("gap")
            if px.height==0:
                continue

            atm=float(px["strike"][0])
            atm_idx=strikes.index(atm)
            if atm_idx<3 or atm_idx>len(strikes)-4:
                continue

            hist=expiry_df.filter(
                (pl.col("strike")==atm) &
                (pl.col("timestamp")>= (et-pd.Timedelta(minutes=30)).to_datetime64()) &
                (pl.col("timestamp")<=et.to_datetime64())
            ).select(["timestamp","option_type","close"])
            hp=hist.pivot(values="close",index="timestamp",columns="option_type",aggregate_function="first").sort("timestamp")
            if hp.height<15 or "CE" not in hp.columns or "PE" not in hp.columns:
                continue
            forward=hp.with_columns((pl.lit(atm)+pl.col("CE")-pl.col("PE")).alias("fwd"))["fwd"].to_numpy()
            rv=float(pd.Series(forward).pct_change().dropna().std()*np.sqrt(252*375))
            fwd_entry=float(forward[-1])
            years=max((pd.Timestamp(expiry)-et)/pd.Timedelta(days=365.25),1/3650)

            # ATM straddle only for VRP filter. Exact IV estimation is optional at this stage;
            # use an ATM-forward approximation stable enough for screening.
            straddle=float(px.filter(pl.col("strike")==atm)["CE"][0] + px.filter(pl.col("strike")==atm)["PE"][0])
            iv_approx=straddle/(fwd_entry*np.sqrt(2*years/np.pi)) if fwd_entry>0 else np.nan
            vrp=iv_approx-rv if np.isfinite(iv_approx) else np.nan

            first15=expiry_df.filter(
                (pl.col("strike")==atm) &
                (pl.col("timestamp")>=pd.Timestamp(day).to_datetime64()+np.timedelta64(9*60+15,"m")) &
                (pl.col("timestamp")<pd.Timestamp(day).to_datetime64()+np.timedelta64(9*60+30,"m"))
            )
            first15_range=np.nan
            if first15.height:
                fp=first15.select(["timestamp","option_type","close"]).pivot(values="close",index="timestamp",columns="option_type",aggregate_function="first")
                if "CE" in fp.columns and "PE" in fp.columns:
                    vals=(fp["CE"]+fp["PE"]).to_numpy()
                    if len(vals):
                        first15_range=float((np.nanmax(vals)-np.nanmin(vals))/straddle) if straddle else np.nan

            for wing_step in (1,2,3):
                lc_strike=strikes[atm_idx-wing_step]
                lp_strike=strikes[atm_idx+wing_step]
                # For an iron fly: short ATM CE/PE, long lower PE and long upper CE.
                legs=expiry_df.filter(
                    (pl.col("strike").is_in([atm,lc_strike,lp_strike])) &
                    (pl.col("timestamp")>et.to_datetime64()) &
                    (pl.col("timestamp")<=(et+pd.Timedelta(minutes=180)).to_datetime64())
                ).select(["timestamp","strike","option_type","high","low","close"])
                p=legs.to_pandas()
                if p.empty:
                    continue
                pv=p.pivot_table(index="timestamp",columns=["strike","option_type"],values=["high","low","close"],aggfunc="first")
                needed=[
                    ("high",atm,"CE"),("high",atm,"PE"),("low",lc_strike,"PE"),("low",lp_strike,"CE"),
                    ("low",atm,"CE"),("low",atm,"PE"),("high",lc_strike,"PE"),("high",lp_strike,"CE"),
                    ("close",atm,"CE"),("close",atm,"PE"),("close",lc_strike,"PE"),("close",lp_strike,"CE")
                ]
                if any(k not in pv.columns for k in needed):
                    continue

                entry_snap=px.filter(pl.col("strike").is_in([atm,lc_strike,lp_strike]))
                def first_px(s,typ):
                    z=q.filter((pl.col("strike")==s)&(pl.col("option_type")==typ)).select(pl.col("close").first())
                    return float(z.item()) if z.height else np.nan
                sc=first_px(atm,"CE"); sp=first_px(atm,"PE"); lc=first_px(lc_strike,"PE"); lp=first_px(lp_strike,"CE")
                if not np.isfinite(sc+sp-lc-lp) or sc+sp-lc-lp<=0:
                    continue

                observations.append({
                    "date":day,"entry":entry_label,"wing_step":wing_step,
                    "atm":atm,"lc":lc_strike,"lp":lp_strike,"expiry":expiry,
                    "credit":sc+sp-lc-lp,"vrp":vrp,"first15_range":first15_range,
                    "lot":nifty_lot_size(day),"pivot":pv,"entry_legs":(sc,sp,lc,lp)
                })

    return observations, len(dates)


def simulate(obs, stop_mult, target_decay, hold):
    p=obs["pivot"].iloc[:hold]
    credit=obs["credit"]
    stop_value=credit*stop_mult
    target_value=credit*(1-target_decay)
    exit_value=None; reason="time"; exit_ts=None
    for ts,r in p.iterrows():
        high_val=float(r[("high",obs["atm"],"CE")]+r[("high",obs["atm"],"PE")]-r[("low",obs["lc"],"PE")]-r[("low",obs["lp"],"CE")])
        low_val=float(r[("low",obs["atm"],"CE")]+r[("low",obs["atm"],"PE")]-r[("high",obs["lc"],"PE")]-r[("high",obs["lp"],"CE")])
        close_val=float(r[("close",obs["atm"],"CE")]+r[("close",obs["atm"],"PE")]-r[("close",obs["lc"],"PE")]-r[("close",obs["lp"],"CE")])
        if high_val>=stop_value:
            exit_value=stop_value; reason="stop"; exit_ts=ts; break
        if low_val<=target_value:
            exit_value=target_value; reason="target"; exit_ts=ts; break
        exit_value=close_val; exit_ts=ts
    if exit_value is None:
        return None
    r=p.loc[exit_ts]
    scx=float(r[("close",obs["atm"],"CE")]); spx=float(r[("close",obs["atm"],"PE")])
    lcx=float(r[("close",obs["lc"],"PE")]); lpx=float(r[("close",obs["lp"],"CE")])
    return exit_value,reason,(scx,spx,lcx,lpx)


def main(path,out):
    df=load(path)
    obs,calendar_days=prepare_observations(df)
    cm=OptionCostModel()
    configs=[Core(e,w,s,t,h) for e in ("09:30:00","09:45:00","10:00:00") for w in (1,2,3) for s in (1.3,1.5,1.7) for t in (0.25,0.40,0.55) for h in (60,120,180)]
    results=[]
    for cfg in configs:
        daily={}
        trades=0
        for o in obs:
            if (o["entry"],o["wing_step"])!=(cfg.entry,cfg.wing_step):
                continue
            ret=simulate(o,cfg.stop_mult,cfg.target_decay,cfg.hold)
            if ret is None:
                continue
            exit_value,reason,legs=ret
            pnl=net_credit_pnl(o["credit"],exit_value,o["lot"],cm,*o["entry_legs"],*legs)
            daily[o["date"]]=daily.get(o["date"],0)+pnl
            trades+=1
        if trades < max(80,int(calendar_days*0.5)):
            continue
        d=pd.Series(0.0,index=pd.Index(sorted(set(x["date"] for x in obs))))
        for k,v in daily.items(): d.loc[k]=v
        eq=d.cumsum(); dd=eq-eq.cummax(); wins=d[d>0].sum(); losses=-d[d<0].sum()
        results.append({
            "entry":cfg.entry,"wing_step":cfg.wing_step,"stop_mult":cfg.stop_mult,
            "target_decay":cfg.target_decay,"hold":cfg.hold,"trades":trades,
            "coverage":trades/calendar_days,"mean_day_net":float(d.mean()),"median_day_net":float(d.median()),
            "p10_day_net":float(d.quantile(0.10)),"positive_day_rate":float((d>0).mean()),
            "max_drawdown":float(dd.min()),"profit_factor":float(wins/losses) if losses else 999.0
        })

    board=pd.DataFrame(results)
    if not board.empty:
        board=board.sort_values(["mean_day_net","positive_day_rate","max_drawdown"],ascending=[False,False,False])
    out.mkdir(parents=True,exist_ok=True)
    board.head(250).to_csv(out/"ironfly_leaderboard.csv",index=False)
    summary={
        "dataset":str(path),"calendar_days":calendar_days,"observations":len(obs),
        "variants_tested":len(configs),"target_daily_net_inr":1000.0,
        "target_qualified_count":int((board["mean_day_net"]>=1000).sum()) if not board.empty else 0,
        "best":board.iloc[0].to_dict() if not board.empty else None
    }
    (out/"ironfly_summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))


if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("reports")); a=ap.parse_args(); main(a.data,a.out)
