from pathlib import Path
import argparse
import polars as pl
import pyarrow.parquet as pq
import pyarrow as pa
import pyarrow.compute as pc

ap=argparse.ArgumentParser()
ap.add_argument("--data",type=Path,required=True)
args=ap.parse_args()

cols=["date","timestamp","expiry","strike","option_type","close","source"]
table=pq.read_table(args.data,columns=cols)
idx=table.schema.get_field_index("timestamp")
t=table.schema.field("timestamp").type
if pa.types.is_timestamp(t) and t.tz:
    raw=pc.cast(table["timestamp"],pa.int64())
    raw=pc.add(raw,pa.scalar(19800000000,pa.int64()))
    table=table.set_column(idx,"timestamp",pc.cast(raw,pa.timestamp("us")))

df=pl.from_arrow(table).with_columns([
    pl.col("date").cast(pl.Date),
    pl.col("timestamp").cast(pl.Datetime("us")),
    pl.col("expiry").cast(pl.Date),
    pl.col("strike").cast(pl.Float64),
    pl.col("option_type").cast(pl.String).str.to_uppercase().replace({"CALL":"CE","PUT":"PE","C":"CE","P":"PE"}),
    pl.col("close").cast(pl.Float64)
])
print("rows",df.height)
print("dates",df.select(pl.col("date").min().alias("date_min"),pl.col("date").max().alias("date_max")))
print("timestamp",df.select(pl.col("timestamp").min().alias("ts_min"),pl.col("timestamp").max().alias("ts_max")))
print("types",df.group_by("option_type").len().sort("len"))
print("expiry range",df.select(pl.col("expiry").min().alias("expiry_min"),pl.col("expiry").max().alias("expiry_max")))
q=df.filter((pl.col("date")==pl.lit("2025-01-02").str.to_date()) & (pl.col("timestamp").dt.hour()>=9) & (pl.col("timestamp").dt.hour()<=10))
print("2025-01-02 09-10 rows",q.height)
print(q.select(["timestamp","expiry","strike","option_type","close"]).head(30))
if q.height:
    print("common strikes",q.filter(pl.col("option_type")=="CE").select("strike").unique().join(q.filter(pl.col("option_type")=="PE").select("strike").unique(),on="strike",how="inner"))
