from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from research.phase3f_option_microstructure import audit


def write_sample(path: Path, *, negative_volume: bool = False) -> None:
    n = 3
    volume = [10, 20, -30] if negative_volume else [10, 20, 30]
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2025-01-01 03:45:00", periods=n, freq="min"),
            "date": pd.date_range("2025-01-01", periods=n, freq="min").date,
            "open": [100.0, 101.0, 102.0],
            "high": [101.0, 102.0, 103.0],
            "low": [99.0, 100.0, 101.0],
            "close": [100.5, 101.5, 102.5],
            "iv": [20.0, 20.5, 21.0],
            "volume": volume,
            "oi": [1000, 1100, 1200],
            "strike_price": [100.0, 100.0, 100.0],
            "spot": [100.0, 100.2, 100.4],
            "expiry_type": ["WEEK"] * n,
            "strike_type": ["ATM"] * n,
            "option_type": ["CALL"] * n,
        }
    )
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path)


def test_audit_reads_multiple_files_and_passes(tmp_path: Path) -> None:
    write_sample(tmp_path / "a.parquet")
    write_sample(tmp_path / "b.parquet")
    result = audit(tmp_path)
    assert result["status"] == "PASS"
    assert result["files"] == 2
    assert result["rows"] == 6
    assert result["unique_days"] == 1


def test_audit_quarantines_negative_volume(tmp_path: Path) -> None:
    write_sample(tmp_path / "bad.parquet", negative_volume=True)
    result = audit(tmp_path)
    assert result["status"] == "QUARANTINE_DATA_QUALITY"
    assert result["quality_counters"]["negative_volume"] == 1
