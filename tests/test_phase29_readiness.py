from research.phase29_readiness import classify


def test_index_family_requires_both_pinned_partitions():
    inv = {
        "trademarkk": {"paths": {"options/NIFTY": {"status": "PRESENT", "file_count": 80, "parquet_file_count": 80}, "stocks_options": {"status": "PRESENT", "file_count": 2}}},
        "rissin": {"paths": {"upstox_intraday/NIFTY": {"status": "PRESENT", "file_count": 2, "parquet_file_count": 2}}},
    }
    status, blocker, _ = classify("iron_fly", inv)
    assert status == "PRELIMINARY_FEASIBLE"
    assert blocker == "INDEX_1M_PINNED_SOURCE_PRESENT"


def test_stock_option_family_is_never_ready_without_strategy_specific_join():
    inv = {
        "trademarkk": {"paths": {"stocks_options": {"status": "PRESENT", "file_count": 200, "parquet_file_count": 200}, "options/NIFTY": {"status": "PRESENT", "file_count": 1, "parquet_file_count": 1}}},
        "rissin": {"paths": {"upstox_intraday/NIFTY": {"status": "PRESENT", "file_count": 1, "parquet_file_count": 1}}},
    }
    status, blocker, _ = classify("covered_call", inv)
    assert status == "DATA_LIMITED"
    assert blocker == "STOCK_OPTIONS_NEED_RULE_SPECIFIC_CONTRACT_COVERAGE"


def test_leaps_is_data_limited():
    inv = {"trademarkk": {"paths": {}}, "rissin": {"paths": {}}}
    status, blocker, _ = classify("leaps|straddle", inv)
    assert status == "DATA_LIMITED"
    assert blocker == "LONG_DATED_CONTINUITY_NOT_VERIFIED"


def test_unresolved_is_blocked():
    inv = {"trademarkk": {"paths": {}}, "rissin": {"paths": {}}}
    status, blocker, _ = classify("unresolved", inv)
    assert status == "UNRESOLVED"
    assert blocker == "SOURCE_RULE_UNRESOLVED"
