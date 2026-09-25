from pathlib import Path
import duckdb
import importlib.util
import pandas as pd

spec=importlib.util.spec_from_file_location('p25',Path('research/phase25_falcon_rissin.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def test_grid_is_frozen(): assert len(m.variant_grid())==270
def test_offsets(): assert m.expiry_offsets()==(-4,-3,-1)
def test_lot_sizes():
 assert m.lot_size('2024-04-25')==50
 assert m.lot_size('2024-11-21')==75
 assert m.lot_size('2026-01-06')==65
def test_pin(): assert m.RISSIN_REVISION.startswith('78b1c546')

def test_series_spans_entry_to_exit_days():
    conn=duckdb.connect()
    rows=[]
    for ts in ["2024-10-30 09:31:00","2024-10-31 09:31:00"]:
        rows.append({
            "timestamp":ts,
            "date":ts[:10],
            "expiry":"2024-11-07",
            "strike":24000,
            "option_type":"CE",
            "open":100.0,
            "close":101.0,
            "granularity":"1min",
        })
    conn.register("bars",pd.DataFrame(rows))
    start=pd.Timestamp("2024-10-30 09:31:00")
    end=pd.Timestamp("2024-10-31 15:15:00")
    out=m.series(conn,"bars","2024-10-30","2024-11-07",24000,"CE",start,end)
    assert set(out.ts.dt.date)=={start.date(),end.date()}


def test_target_strike_is_scalar_safe():
    df = pd.DataFrame([
        {"option_type": "CE", "strike": 24000.0, "open_px": 25.0, "close_px": 25.0},
        {"option_type": "CE", "strike": 24100.0, "open_px": 26.0, "close_px": 26.0},
        {"option_type": "PE", "strike": 24000.0, "open_px": 25.0, "close_px": 25.0},
    ])
    row = m.target(df, "CE", 25.0)
    assert row is not None
    assert float(row["strike"]) == 24000.0


def test_src_quotes_both_parquet_paths(tmp_path):
    root = tmp_path / 'upstox_intraday' / 'NIFTY'
    root.mkdir(parents=True)
    (root / 'NIFTY_2024.parquet').touch()
    (root / 'NIFTY_2025.parquet').touch()
    s = m.src(tmp_path)
    assert "NIFTY_2024.parquet'" in s
    assert "NIFTY_2025.parquet'" in s
    assert s.count("'") >= 4
