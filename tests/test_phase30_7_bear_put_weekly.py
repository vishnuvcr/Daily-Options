import pandas as pd
from datetime import date
from research.phase30_7_bear_put_weekly import lot_size, round_to_50, strike_pair

def test_lot_schedule():
    assert lot_size(date(2025,12,30)) == 75
    assert lot_size(date(2026,1,6)) == 65

def test_round_to_50():
    assert round_to_50(26299) == 26300
    assert round_to_50(26326) == 26350

def test_strike_configs():
    assert strike_pair(26300,"ATM_W50") == (26300,26250)
    assert strike_pair(26300,"OTM1_W50") == (26250,26200)
    assert strike_pair(26300,"ATM_W100") == (26300,26200)
    assert strike_pair(26300,"OTM1_W100") == (26250,26150)
