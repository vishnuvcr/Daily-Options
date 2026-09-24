from pathlib import Path
import inspect
from research.phase17_nifty_exact_expiry_premium_skew import variant_grid, expiry_for_day

def test_variant_count():
    assert len(variant_grid()) == 384

def test_expiry_selection():
    files=[(Path("2025-01-02.parquet").stem,"/x")]
    pairs=[(__import__("datetime").date(2025,1,2),Path("/x"))]
    assert expiry_for_day(pairs,__import__("datetime").date(2025,1,1))[0].isoformat()=="2025-01-02"

def test_variant_dimensions_are_frozen():
    fields=set(variant_grid()[0])
    assert {"entry_time","skew","jump","rv","width","hold","stop","side"} <= fields

def test_active_day_target_metric_in_source():
    src=inspect.getsource(__import__("research.phase17_nifty_exact_expiry_premium_skew",fromlist=["run"]))
    assert "mean_active_day_net" in src
    assert ">=1000" in src
