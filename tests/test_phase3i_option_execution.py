import pandas as pd

from research.phase3i_option_execution import (
    HOLDS,
    EXPIRIES,
    WIDTH_STEPS,
    SIGNAL_SPECS,
    build_signal_events,
    signal_variant_key,
)
from research.zenodo_option_source import (
    expiry_type,
    parse_strike_type,
)


def test_option_grid_is_bounded():
    assert len(SIGNAL_SPECS) == 2
    assert EXPIRIES == ("WEEK", "MONTH")
    assert WIDTH_STEPS == (1, 2)
    assert HOLDS == (5, 10, 15)


def test_signal_variant_keys_are_stable():
    assert signal_variant_key(SIGNAL_SPECS[0]) == (
        '{"feature": "lead_gap", "lookback": 3, "mode": "continuation", "threshold_bps": 10.0}'
    )


def test_signal_builder_uses_first_event_per_day():
    idx = pd.date_range("2019-01-02 09:30", periods=4, freq="min")
    spot = pd.DataFrame({
        "datetime": idx,
        "trade_date": idx.date,
        "close": [100, 100.1, 100.2, 100.3],
    })
    fut = spot.copy()
    fut["close"] = [100, 100.2, 100.4, 100.6]
    out = build_signal_events(spot, fut)
    assert out["trade_date"].nunique() <= 1


def test_zenodo_expiry_classification():
    assert expiry_type(pd.Timestamp("2019-12-26").date()) == "MONTH"
    assert expiry_type(pd.Timestamp("2019-12-19").date()) == "WEEK"


def test_zenodo_filename_strike_and_type():
    assert parse_strike_type(pd.Path if False else __import__("pathlib").Path("Nifty11200CE.xlsx")) == (11200.0, "CALL")
    assert parse_strike_type(__import__("pathlib").Path("Nifty11200PE.xlsx")) == (11200.0, "PUT")


def test_variant_identity_excludes_trade_id():
    from research.phase3i_option_execution import SIGNAL_SPECS
    assert signal_variant_key(SIGNAL_SPECS[0]) != signal_variant_key(SIGNAL_SPECS[1])


def test_entry_schema_persists_wing_strike():
    import inspect
    from research.phase3i_option_execution import simulate
    assert "wing_strike" in inspect.getsource(simulate)


def test_zenodo_txt_contract_schema(tmp_path):
    p = tmp_path / "NiftyOptions 2017.zip" / "December 2017.zip" / "CE 10550.txt"
    p.parent.mkdir(parents=True)
    p.write_text(
        "CE 10550,2017/11/15,09:26,50,50,50,50,75\n"
        "CE 10550,2017/11/15,09:27,51,52,50,51.5,150\n",
        encoding="utf-8",
    )
    from research.zenodo_option_source import parse_expiry_date, parse_strike_type, read_contract_file
    assert parse_strike_type(p) == (10550.0, "CALL")
    assert parse_expiry_date(p) == pd.Timestamp("2017-12-28").date()
    out = read_contract_file(p)
    assert len(out) == 2
    assert out.iloc[0]["close"] == 50.0


def test_zenodo_range_folder_expiry_inference():
    from pathlib import Path
    from research.zenodo_option_source import parse_expiry_date
    p = Path("NiftyOptions 2019.zip/December 2019.zip/December/CSV 22-10-19 to 26-12-19 (Expiry Day).zip/CE 12000.csv")
    assert parse_expiry_date(p) == pd.Timestamp("2019-12-26").date()
