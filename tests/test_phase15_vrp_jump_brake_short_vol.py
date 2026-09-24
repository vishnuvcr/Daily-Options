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
