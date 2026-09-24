from research.phase15_vrp_jump_brake_short_vol import variant_grid

def test_grid_count():
    assert len(variant_grid()) == 288

def test_grid_dimensions():
    g=variant_grid()
    assert {x['vrp_threshold'] for x in g}=={0.0,2.0,4.0}
    assert {x['jump_max'] for x in g}=={0.0025,0.0040}
    assert {x['structure'] for x in g}=={'STRADDLE','IRONFLY'}
    assert {x['expiry_type'] for x in g}=={'WEEK','MONTH'}


def test_required_files_sql_is_duckdb_list():
    from pathlib import Path
    from research.phase15_vrp_jump_brake_short_vol import required_files_sql
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for expiry in ("WEEK","MONTH"):
            (root/expiry).mkdir(parents=True, exist_ok=True)
            for name in ("ATM_CE.parquet","ATM_PE.parquet","ATM+2_CE.parquet","ATM+2_PE.parquet","ATM-2_CE.parquet","ATM-2_PE.parquet"):
                (root/expiry/name).write_bytes(b"")
        sql_list = required_files_sql(root)
        assert sql_list.startswith("[")
        assert sql_list.endswith("]")
        assert "'WEEK/ATM_CE.parquet'" in sql_list or "ATM_CE.parquet" in sql_list


def test_required_files_feature_only_uses_four_atm_files():
    from pathlib import Path
    from research.phase15_vrp_jump_brake_short_vol import required_files_sql
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        for expiry in ("WEEK","MONTH"):
            (root/expiry).mkdir(parents=True,exist_ok=True)
            for name in ("ATM_CE.parquet","ATM_PE.parquet","ATM+2_CE.parquet","ATM+2_PE.parquet","ATM-2_CE.parquet","ATM-2_PE.parquet"):
                (root/expiry/name).write_bytes(b"")
        q=required_files_sql(root, feature_only=True)
        assert "ATM_CE.parquet" in q and "ATM_PE.parquet" in q
        assert "ATM+2_CE.parquet" not in q
        assert "ATM-2_PE.parquet" not in q


def test_expiry_shards_have_equal_cell_counts():
    g=variant_grid()
    assert sum(x['expiry_type']=='WEEK' for x in g)==144
    assert sum(x['expiry_type']=='MONTH' for x in g)==144


def test_select_signals_uses_ist_time():
    import pandas as pd
    from research.phase15_vrp_jump_brake_short_vol import select_signals, variant_grid
    v=[x for x in variant_grid() if x['expiry_type']=='WEEK' and x['entry_time']=='09:30:00' and x['vrp_threshold']==0.0 and x['jump_max']==0.0040 and x['structure']=='STRADDLE' and x['hold_minutes']==30 and x['stop_ratio']==1.30][0]
    f=pd.DataFrame([{'trade_date':pd.Timestamp('2020-01-02').date(),'datetime':pd.Timestamp('2020-01-02 04:00:00'),'expiry_type':'WEEK','spot':100.0,'vrp':1.0,'abs_ret15':0.001}])
    y=select_signals(f,v)
    assert len(y)==1


def test_vectorized_simulation_returns_trade():
    import pandas as pd
    from research.phase15_vrp_jump_brake_short_vol import simulate
    signal=pd.Series({
        'trade_date':pd.Timestamp('2020-01-02').date(),
        'datetime':pd.Timestamp('2020-01-02 04:00:00'),
        'expiry_type':'WEEK','vrp':2.0,'abs_ret15':0.001})
    setup={
        'entry_time':pd.Timestamp('2020-01-02 04:01:00'),
        'call_strike':100.0,'put_strike':100.0,
        'call_entry':50.0,'put_entry':50.0,
        'call_wing_strike':105.0,'put_wing_strike':95.0,
        'call_wing_entry':20.0,'put_wing_entry':20.0}
    bars=pd.DataFrame({
        'datetime':[pd.Timestamp('2020-01-02 04:01:00'),pd.Timestamp('2020-01-02 04:02:00')],
        'call_high':[50.0,55.0],'put_high':[50.0,55.0],
        'call_low':[45.0,45.0],'put_low':[45.0,45.0],
        'call_close':[48.0,52.0],'put_close':[48.0,52.0],
        'call_wing_high':[20.0,22.0],'put_wing_high':[20.0,22.0],
        'call_wing_low':[18.0,18.0],'put_wing_low':[18.0,18.0],
        'call_wing_close':[19.0,21.0],'put_wing_close':[19.0,21.0]})
    out=simulate(signal,setup,bars,'STRADDLE',1.3,0.20)
    assert out is not None
