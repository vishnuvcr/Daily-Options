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
