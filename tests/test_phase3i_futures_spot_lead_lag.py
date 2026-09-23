from pathlib import Path
import pandas as pd

from research.phase3i_futures_spot_lead_lag import (
    diagnostic_grid,
    normalize_table,
)


def test_phase3i_grid_is_bounded():
    grid = diagnostic_grid()
    assert len(grid) == 72
    assert {v.lookback for v in grid} == {1, 3, 5}
    assert {v.threshold_bps for v in grid} == {0.0, 2.0, 5.0, 10.0}
    assert {v.mode for v in grid} == {"continuation", "contrarian"}
    assert {v.feature for v in grid} == {"futures_return", "lead_gap", "basis_change"}


def test_normalize_table_builds_datetime():
    df = pd.DataFrame({
        "trade date": ["2020-01-02"],
        "trade time": ["09:15"],
        "Open": [100.0],
        "High": [101.0],
        "Low": [99.0],
        "Close": [100.5],
        "Volume": [10],
    })
    out = normalize_table(df)
    assert "datetime" in out.columns
    assert pd.Timestamp("2020-01-02 09:15:00") == out.iloc[0]["datetime"]


def test_normalize_table_rejects_non_price_rows():
    df = pd.DataFrame({"Date": ["2020-01-02"], "Time": ["09:15"], "Close": [-1]})
    out = normalize_table(df)
    assert out.empty


def test_normalize_table_accepts_trade_dt():
    df = pd.DataFrame({
        "trade dt": ["2019-01-02"],
        "trade time": ["09:15"],
        "Open": [100.0],
        "High": [101.0],
        "Low": [99.0],
        "Close": [100.5],
    })
    out = normalize_table(df)
    assert pd.Timestamp("2019-01-02 09:15:00") == out.iloc[0]["datetime"]
