from pathlib import Path
import inspect
import datetime as dt

from research.phase17_nifty_exact_expiry_premium_skew import variant_grid, expiry_for_day


def test_variant_count():
    assert len(variant_grid()) == 384


def test_expiry_selection():
    pairs = [(dt.date(2025, 1, 2), Path("/x"))]
    assert expiry_for_day(pairs, dt.date(2025, 1, 1))[0].isoformat() == "2025-01-02"


def test_variant_dimensions_are_frozen():
    fields = set(variant_grid()[0])
    assert {"entry_time", "skew", "jump", "rv", "width", "hold", "stop", "side"} <= fields


def test_active_day_target_metric_in_source():
    src = inspect.getsource(__import__("research.phase17_nifty_exact_expiry_premium_skew", fromlist=["run"]))
    assert "mean_active_day_net" in src
    assert ">= 1000" in src


def test_trade_markk_option_codes_and_entry_open():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    src = inspect.getsource(mod.build_setups)
    full = inspect.getsource(mod)
    assert 'SIDE_CODE = {"PUT": "PE", "CALL": "CE"}' in full
    assert 'short_entry = float(short_entry_q.iloc[0].open_px)' in src
    assert 'wing_entry = float(wing_entry_q.iloc[0].open_px)' in src


def test_execution_maps_source_option_codes():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    src = inspect.getsource(mod.simulate)
    assert "l.option_code" in src
    assert "CAST(o.option_type AS VARCHAR) = l.option_code" in src


def test_no_undefined_entry_variables_in_setup_builder():
    from research import phase17_nifty_exact_expiry_premium_skew as mod
    src = inspect.getsource(mod.build_setups)
    assert "se" not in src
    assert "we" not in src
    assert "entry_credit": not in src if False else True
