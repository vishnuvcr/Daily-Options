import inspect
from research import phase19_nifty_short_strangle_regime as mod


def test_variant_grid_count():
    assert len(mod.variant_grid()) == 144


def test_cost_model_has_short_strangle():
    import research.cost_model as cm
    assert hasattr(cm.OptionCostModel, "short_strangle_net_pnl")


def test_filter_uses_explicit_columns():
    src = inspect.getsource(mod.filter_setups)
    assert 'setups["short_offset"]' in src
    assert 'setups["spot_ret10"]' in src
    assert 'setups["rv_ratio"]' in src


def test_empty_setup_filter_is_safe():
    import pandas as pd
    assert mod.filter_setups(pd.DataFrame()).empty


def test_setup_uses_source_native_option_codes():
    src = inspect.getsource(mod.build_setups)
    assert '(q["option_type"] == "PE")' in src
    assert '(q["option_type"] == "CE")' in src


def test_target_metric_is_active_day():
    src = inspect.getsource(mod.summarize)
    assert '"mean_active_day_net"' in src
    assert '>= 1000' in src


def test_spot_alias_is_normalized():
    src = inspect.getsource(mod.load_spot)
    assert 'spot_close' in src


def test_exact_quote_loader_uses_direct_local_time_window():
    src=inspect.getsource(mod.load_exact_quotes)
    assert 'strftime("timestamp",\'%H:%M:%S\') >= \'14:30:00\'' in src
    assert 'strftime("timestamp",\'%H:%M:%S\') <= \'15:03:00\'' in src


def test_direct_quote_window_uses_timezone_safe_strftime():
    src=inspect.getsource(mod.load_exact_quotes)
    assert 'strftime("timestamp",\'%H:%M:%S\')' in src
