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


def test_simulation_uses_variant_hold_and_risk_without_expansion(tmp_path, monkeypatch):
    import pandas as pd
    import research.phase12_zenodo_pilot as mod

    bars = pd.DataFrame([
        {
            "datetime": pd.Timestamp("2019-04-16 04:31:00"),
            "open_a": 50.0, "high_a": 55.0, "low_a": 49.0, "close_a": 54.0,
            "open_b": 20.0, "high_b": 21.0, "low_b": 19.0, "close_b": 20.0,
        },
        {
            "datetime": pd.Timestamp("2019-04-16 04:32:00"),
            "open_a": 54.0, "high_a": 55.0, "low_a": 53.0, "close_a": 54.0,
            "open_b": 20.0, "high_b": 20.5, "low_b": 19.5, "close_b": 20.0,
        },
    ])
    monkeypatch.setattr(mod, "_merge_leg_bars", lambda *args, **kwargs: bars)
    monkeypatch.setattr(mod, "index_option_lot_size", lambda *args, **kwargs: 75)

    entries = pd.DataFrame([{
        "variant_id": "lw3|z1.50|10:00:00|MONTH|w2|h20|r1",
        "trade_date": "2019-04-16",
        "entry_time": "2019-04-16 04:31:00",
        "direction": "CALL",
        "expiry": "2019-05-30",
        "side": "CE",
        "atm_strike": 11800.0,
        "wing_strike": 11900.0,
        "atm_path": "a.csv",
        "wing_path": "b.csv",
        "spot": 11783.0,
        "hold_minutes": 20,
        "risk_id": 1,
    }])

    out = mod.simulate_unique(entries, tmp_path, 0.20)
    assert len(out) == 1
    assert int(out.iloc[0]["hold_minutes"]) == 20
    assert int(out.iloc[0]["risk_id"]) == 1
