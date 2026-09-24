import pandas as pd

from research.phase12_zenodo_pilot import (
    RISK_PROFILES,
    variant_grid,
    data_gate,
    _last_thursday,
    _utc_naive,
    load_zenodo_market,
    _read_table,
    _standardize_ohlc,
)


def test_variant_count_is_preregistered():
    assert len(variant_grid()) == 288


def test_last_thursday():
    assert _last_thursday(2020, 1) == pd.Timestamp("2020-01-30")
    assert _last_thursday(2020, 4) == pd.Timestamp("2020-04-30")


def test_utc_normalization_from_nse_local_time():
    x = pd.Series(pd.to_datetime(["2020-01-02 09:15:00", "2020-01-02 09:16:00"]))
    y = _utc_naive(x)
    assert str(y.iloc[0]) == "2020-01-02 03:45:00"


def test_data_gate_passes_reasonable_overlap():
    dt = pd.date_range("2019-01-01", periods=400, freq="D")
    f = pd.DataFrame({"datetime": dt, "futures_close": 100.0})
    s = pd.DataFrame({"datetime": dt, "spot_close": 100.0})
    g = data_gate(f, s)
    assert g["gate"] == "PASS"


def test_risk_profiles_fixed():
    assert RISK_PROFILES == (
        {"stop_pct": 0.30, "target_pct": 0.60},
        {"stop_pct": 0.50, "target_pct": 1.00},
    )

# helper-dependency trigger checkpoint 2026-09-24


def test_zenodo_known_market_filenames(tmp_path):
    market = tmp_path / "market" / "2019"
    market.mkdir(parents=True)
    rows = "Trade Date,Trade Time,Open,High,Low,Close,Volume\n2019-01-02,09:15:00,100,101,99,100.5,10\n2019-01-02,09:16:00,100.5,101.5,100,101,12\n"
    (market / "NIFTY.csv").write_text(rows)
    (market / "NIFTY_F1.csv").write_text(rows)
    futures, spot = load_zenodo_market(tmp_path / "market")
    assert len(futures) == 2
    assert len(spot) == 2
    assert "futures_close" in futures.columns
    assert "spot_close" in spot.columns

# concurrency-fix trigger checkpoint 2026-09-24


def test_headerless_zenodo_market_row_preserves_first_record(tmp_path):
    market = tmp_path / "market"
    market.mkdir(parents=True)
    raw = "NIFTY,2019/01/01,09:16,10884.1,10885.3,10872.3,10874.5,0,0\nNIFTY,2019/01/01,09:17,10874.1,10879.2,10874.1,10874.9,0,0\n"
    p = market / "NIFTY.csv"
    p.write_text(raw)
    from research.phase12_zenodo_pilot import _standardize_ohlc, _read_table
    out = _standardize_ohlc(_read_table(p))
    assert len(out) == 2
    assert float(out.iloc[0]["close"]) == 10874.5


def test_headerless_zenodo_option_row_parses_ohlc(tmp_path):
    p = tmp_path / "CE 10500.txt"
    p.write_text("2019/01/01,09:16,120.5,121.0,120.0,120.8,100,200\n")
    from research.phase12_zenodo_pilot import _standardize_ohlc, _read_table
    out = _standardize_ohlc(_read_table(p))
    assert len(out) == 1
    assert float(out.iloc[0]["close"]) == 120.8

    
def test_headerless_zenodo_row_maps_to_named_ohlc_columns(tmp_path):
    p = tmp_path / "NIFTY.csv"
    p.write_text(
        "NIFTY,2019/01/01,09:16,10884.1,10885.3,10872.3,10874.5,0,0\n"
        "NIFTY,2019/01/01,09:17,10874.1,10879.2,10874.1,10874.9,0,0\n"
    )
    raw = _read_table(p)
    x = _standardize_ohlc(raw)
    assert list(x.columns) == ["datetime", "open", "high", "low", "close", "volume"]
    assert float(x.iloc[0]["close"]) == 10874.5


def test_headerless_zenodo_option_row_maps_to_named_ohlc_columns(tmp_path):
    p = tmp_path / "NIFTY11650PE.csv"
    p.write_text(
        "NIFTY11650PE,2019/05/02,09:16,120.5,121.0,119.8,120.2,150,0\n"
    )
    raw = _read_table(p)
    x = _standardize_ohlc(raw)
    assert float(x.iloc[0]["open"]) == 120.5
    assert float(x.iloc[0]["close"]) == 120.2


def test_lead_features_use_ist_entry_clock():
    import pandas as pd
    from research.phase12_zenodo_pilot import lead_features

    dt = pd.date_range("2019-01-02 03:44:00", periods=2, freq="1min")
    futures = pd.DataFrame({"datetime": dt, "futures_close": [100.0, 100.2]})
    spot = pd.DataFrame({"datetime": dt, "spot_close": [100.0, 100.1]})
    out = lead_features(futures, spot, 1)
    assert out.iloc[-1]["trade_time_ist"] == "09:15:00"
    assert out.iloc[-1]["trade_time_utc"] == "03:45:00"
