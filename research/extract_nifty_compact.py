from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


def read_source(path: Path) -> pl.DataFrame:
    cols=["date","timestamp","expiry","strike","option_type","high","low","close"]
    table=pq.read_table(path,columns=cols)
    idx=table.schema.get_field_index("timestamp")
    ts=table.schema.field("timestamp").type
    if pa.types.is_timestamp(ts) and ts.tz:
        raw=pc.cast(table["timestamp"],pa.int64())
        # Dataset timezone is +05:30; convert epoch to IST wall-clock before removing timezone metadata.
        raw=pc.add(raw,pa.scalar(19800000000,pa.int64()))
        table=table.set_column(idx,"timestamp",pc.cast(raw,pa.timestamp("us")))
    return pl.from_arrow(table).with_columns([
        pl.col("date").cast(pl.Date),
        pl.col("timestamp").cast(pl.Datetime("us")),
        pl.col("expiry").cast(pl.Date),
        pl.col("strike").cast(pl.Float64),
        pl.col("option_type").cast(pl.String).str.to_uppercase(),
        pl.col("high").cast(pl.Float64),
        pl.col("low").cast(pl.Float64),
        pl.col("close").cast(pl.Float64),
    ]).filter(pl.col("option_type").is_in(["CE","PE"]))


def extract(path: Path, out: Path, wing_steps: int = 3) -> dict:
    df=read_source(path)
    # First research window: 09:15-13:15 IST for each trading day.
    start_ns=9*60+15
    end_ns=13*60+15
    df=df.with_columns(
        (pl.col("timestamp").dt.hour()*60 + pl.col("timestamp").dt.minute()).alias("_min")
    ).filter((pl.col("_min")>=start_ns)&(pl.col("_min")<=end_ns)).drop("_min")

    eligible=df.filter(pl.col("expiry")>=pl.col("date"))
    near=eligible.join(
        eligible.group_by("date").agg(pl.col("expiry").min().alias("near_expiry")),
        on="date",
        how="inner",
    ).filter(pl.col("expiry")==pl.col("near_expiry")).drop("near_expiry")

    # Determine an ATM proxy independently for each day using 09:30 parity.
    q=near.filter(
        (pl.col("timestamp").dt.hour()==9) &
        (pl.col("timestamp").dt.minute()>=30) &
        (pl.col("timestamp").dt.minute()<=32)
    ).group_by(["date","strike","option_type"]).agg(pl.col("close").first())
    px=q.pivot(values="close",index=["date","strike"],columns="option_type",aggregate_function="first")
    if "CE" not in px.columns or "PE" not in px.columns:
        raise RuntimeError("09:30 chain does not contain both CE and PE columns")
    px=px.drop_nulls(["CE","PE"]).with_columns((pl.col("CE")-pl.col("PE")).abs().alias("gap"))
    atm=(
        px.sort(["date","gap"])
        .group_by("date",maintain_order=True)
        .first()
        .select(["date","strike"])
        .rename({"strike":"atm"})
    )

    # Keep ATM plus +/- wing_steps available strikes for each day.
    keys=[]
    for row in atm.iter_rows(named=True):
        d=row["date"]; a=float(row["atm"])
        strikes=(near.filter(pl.col("date")==d).select("strike").unique().sort("strike")["strike"].to_list())
        if not strikes:
            continue
        pos=min(range(len(strikes)),key=lambda i:abs(float(strikes[i])-a))
        lo=max(0,pos-wing_steps); hi=min(len(strikes)-1,pos+wing_steps)
        for s in strikes[lo:hi+1]:
            keys.append((d,float(s)))

    keep=pl.DataFrame(keys,schema={"date":pl.Date,"strike":pl.Float64}).unique()
    compact=near.join(keep,on=["date","strike"],how="inner").select(
        ["date","timestamp","expiry","strike","option_type","high","low","close"]
    ).sort(["date","timestamp","strike","option_type"])

    out.parent.mkdir(parents=True,exist_ok=True)
    compact.write_parquet(out,compression="zstd")
    manifest={
        "source":str(path),
        "output":str(out),
        "source_rows":int(df.height),
        "compact_rows":int(compact.height),
        "calendar_days":int(compact.select("date").n_unique()),
        "strikes_per_day_max":2*wing_steps+1,
        "output_bytes":out.stat().st_size,
    }
    Path(out.with_suffix(".json")).write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))
    return manifest


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,default=Path("reports/nifty_2025_compact.parquet"))
    ap.add_argument("--wing-steps",type=int,default=3)
    a=ap.parse_args()
    extract(a.data,a.out,a.wing_steps)
