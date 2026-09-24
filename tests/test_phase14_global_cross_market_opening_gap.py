import pandas as pd
import numpy as np

from research.phase14_global_cross_market_opening_gap import variant_grid, _global_zscore_series, build_features


def test_variant_count():
    assert len(variant_grid()) == 768


def test_global_zscore_uses_only_prior_returns():
    d = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-01","2020-01-02","2020-01-03","2020-01-04"]).date,
        "close": [100.0, 102.0, 104.0, 106.0],
    })
    z = _global_zscore_series(d)
    assert pd.isna(z.iloc[1]["z"])


def test_feature_barrier_uses_ist():
    spot = pd.DataFrame({
        "datetime": pd.to_datetime([
            "2020-01-02 03:44:00","2020-01-02 03:45:00"
        ]),
        "spot_close": [100.0,101.0],
    })
    glob = {
        "SP500": pd.DataFrame({"date":[pd.Timestamp("2019-12-31").date()], "close":[100.0]}),
        "NASDAQ": pd.DataFrame({"date":[pd.Timestamp("2019-12-31").date()], "close":[100.0]}),
        "NIKKEI": pd.DataFrame({"date":[pd.Timestamp("2019-12-31").date()], "close":[100.0]}),
    }
    x = build_features(spot, glob)
    assert x.iloc[-1]["trade_time_ist"] == "09:15:00"
