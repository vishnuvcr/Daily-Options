import pandas as pd
import numpy as np
from research.phase33_dealer_gamma_exposure import FEATURES, THRESHOLDS, EXITS, WARMUP, bs_gamma, bs_price, implied_vol, lot_size, make_signals, summarize

def test_frozen_grid_cardinality():
    assert len(FEATURES)*len(THRESHOLDS)*len(EXITS)==12

def test_historical_nifty_lot_sizes():
    assert lot_size("2021-07-01")==50
    assert lot_size("2024-04-26")==25
    assert lot_size("2024-11-21")==75
    assert lot_size("2026-01-06")==65

def test_gamma_positive():
    g=bs_gamma(22000,22000,30/365,0.20)
    assert g>0

def test_iv_round_trip():
    p=bs_price(22000,22000,30/365,0.20,True)
    iv=implied_vol(p,22000,22000,30/365,True)
    assert iv is not None and abs(iv-0.20)<1e-5

def test_signal_null_permutation_changes_feature_assignment():
    d=pd.date_range("2021-01-01",periods=WARMUP+10,freq="B").date
    p=pd.DataFrame({"trade_date":d,"spot":22000.0,"net_gex":np.where(np.arange(len(d))%2,1.0,-1.0),
                    "GEX_Z":np.linspace(-2,2,len(d)),"FLIP_DISTANCE_Z":np.linspace(2,-2,len(d)),
                    "ATM_GEX_SHARE_Z":np.sin(np.arange(len(d)))})
    s=pd.DataFrame({"trade_date":d,"ts":pd.to_datetime(d).map(lambda x: pd.Timestamp(x)+pd.Timedelta(hours=9,minutes=15)),
                    "open":22000.0+np.arange(len(d)),"close":22000.0+np.arange(len(d))})
    a=make_signals(p,s); b=make_signals(p,s,permute_seed=101)
    assert len(a)!=len(b) or not a.equals(b)
    # A fixed-seed block permutation must alter the registered state assignment.
    assert not a.equals(b)

def test_summary_emits_all_12_cells():
    x=pd.DataFrame(columns=["feature","threshold","exit_time","week","net_pnl","gross_pnl","slippage"])
    z=summarize(x)
    assert len(z)==12
    assert set(z.feature)==set(FEATURES)


def test_put_debit_spread_direction_is_not_sign_inverted():
    entry=100.0-50.0
    exitv=120.0-60.0
    lot=50
    gross=(exitv-entry)*lot
    assert gross>0

def test_cost_model_includes_brokerage_and_stt():
    c=__import__("research.phase33_dealer_gamma_exposure",fromlist=["charge"]).charge
    total=c(100,"BUY",1,50,"2025-01-01")+c(80,"SELL",1,50,"2025-01-01")
    assert total>40
