from research.phase29_2_contract_coverage import classify, expiry_requirement, infer_underlying


def test_explicit_nifty_is_inferred():
    assert infer_underlying("NIFTY Iron Fly", "iron_fly") == "NIFTY"


def test_stock_is_not_called_index():
    assert infer_underlying("Covered Call", "covered_call") == "STOCK"


def test_calendar_requires_multiple_expiries():
    assert expiry_requirement("Cross Calendar Setup", "calendar") == "MULTI_EXPIRY"


def test_leaps_is_long_dated():
    assert expiry_requirement("LEAPS Formula", "leaps") == "LEAPS_OR_LONG_DATED"


def test_unknown_underlying_blocks():
    inv = {"trademarkk": {"paths": {}}, "rissin": {"paths": {}}}
    row = {
        "family_id": "EIG", "video_id": "v1", "title": "Iron Fly",
        "candidate_family_hint": "iron_fly",
        "cluster_confidence": "REVIEW_REQUIRED",
        "source_fidelity": "UNRESOLVED",
    }
    out = classify(row, inv, {"v1"})
    assert out["readiness_state"] == "UNDERLYING_UNRESOLVED"
    assert out["backtest_allowed"] == "NO"


def test_stock_has_primary_but_no_independent_validation():
    inv = {
        "trademarkk": {"paths": {"stocks_options": {"parquet_file_count": 100}}},
        "rissin": {"paths": {}},
    }
    row = {
        "family_id": "EIG", "video_id": "v1", "title": "Covered Call",
        "candidate_family_hint": "covered_call",
        "cluster_confidence": "REVIEW_REQUIRED",
        "source_fidelity": "UNRESOLVED",
    }
    out = classify(row, inv, {"v1"})
    assert out["readiness_state"] == "DATA_PARTIAL_INDEPENDENT_GAP"
