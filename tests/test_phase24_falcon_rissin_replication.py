import inspect
from datetime import date

from research.phase24_falcon_rissin_replication import (
    cost,
    lot_size,
    variant_grid,
    build_schedule,
)


def test_variant_count_is_frozen():
    assert len(variant_grid()) == 270


def test_lot_size_schedule_matches_phase24():
    assert lot_size(date(2024, 10, 1)) == 25
    assert lot_size(date(2024, 11, 21)) == 75
    assert lot_size(date(2026, 1, 6)) == 65


def test_source_primary_premium_and_far_mode_are_frozen():
    grid = variant_grid()
    assert any(v.target_premium == 25.0 for v in grid)
    assert any(v.far_mode == "DIAGONAL_PREMIUM" for v in grid)


def test_schedule_uses_expiry_relative_offsets():
    src = inspect.getsource(build_schedule)
    assert "expiry - 4 sessions" in src
    assert "adjustment = prior[-3]" in src
    assert "exit = prior[-1]" in src
    assert "Wednesday entry -> Thursday adjustment -> Monday exit" in src


def test_cost_model_is_date_aware_and_includes_brokerage():
    src = inspect.getsource(cost)
    assert "40.0" in src
    assert "0.0015" in src
    assert "0.001" in src
    assert "2026, 4, 1" in src
    assert "2026, 3, 1" in src
    assert "0.000355299" in src
    assert "0.18" in src


def test_rissin_reader_uses_exact_expiry_and_ist_timestamp_fields():
    from research.phase24_falcon_rissin_replication import load_entry_chain
    src = inspect.getsource(load_entry_chain)
    assert "TRY_CAST(expiry AS DATE)" in src
    assert "timestamp" in src
    assert "option_type" in src


def test_one_strike_adjustment_is_directional():
    from research.phase24_falcon_rissin_replication import choose_wings
    ce, pe = choose_wings(
        strikes={"CE":[24000,24050,24100], "PE":[23800,23850,23900]},
        short_ce=24050,
        short_pe=23850,
    )
    assert ce == 24100
    assert pe == 23800