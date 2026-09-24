
    
def test_feature_query_derives_trade_date_from_ist_timestamp(tmp_path):
    from research.phase16_iv_skew_tail_credit import feature_query
    for name in [
        "ATM+2_CE.parquet","ATM+2_PE.parquet","ATM-2_CE.parquet","ATM-2_PE.parquet",
        "ATM+3_CE.parquet","ATM+3_PE.parquet","ATM-3_CE.parquet","ATM-3_PE.parquet",
        "ATM+4_CE.parquet","ATM+4_PE.parquet","ATM-4_CE.parquet","ATM-4_PE.parquet",
    ]:
        p=tmp_path/"WEEK"/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(b"")
    q=feature_query(tmp_path,"WEEK")
    assert "CAST(CAST(datetime AS TIMESTAMP)+INTERVAL '5 hours 30 minutes' AS DATE) trade_date" in q
    assert "CAST(date AS DATE) trade_date" not in q
    assert "CAST(expiry AS DATE) >= CAST(date AS DATE)" not in q
    assert "CAST(expiry AS DATE) >= CAST(CAST(datetime AS TIMESTAMP)+INTERVAL '5 hours 30 minutes' AS DATE)" in q


def test_outcome_cache_carries_actual_expiry_through_simulation():
    from research import phase16_iv_skew_tail_credit as mod
    import inspect
    src=inspect.getsource(mod.run)
    assert "set_index(['trade_date','entry_time','expiry','expiry_type','side','width'])" in src
    assert "win.expiry==u.expiry" in src
    assert "keycols=['trade_date','datetime','expiry','expiry_type']" in src


def test_target_gate_is_active_day_metric():
    from research import phase16_iv_skew_tail_credit as mod
    import inspect
    src=inspect.getsource(mod.run)
    assert "'target_metric':'mean_active_day_net'" in src
    assert "b.mean_active_day_net>=1000" in src
