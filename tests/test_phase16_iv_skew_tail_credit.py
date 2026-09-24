
    
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
