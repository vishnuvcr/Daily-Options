import math
from datetime import date
from research.phase30_2_air_defense_iron_condor import expected_move, select_call_strike, select_put_strike, lot_size

def test_expected_move():
    got=expected_move(24000.0,18.0,5*24*60,1.0)
    expected=24000.0*0.18*math.sqrt((5*24*60)/(365*24*60))
    assert abs(got-expected)<1e-9

def test_short_strikes():
    strikes=[23500,23800,24000,24200,24500,25000]
    assert select_call_strike(strikes,24000,450)==24500
    assert select_put_strike(strikes,24000,450)==23500

def test_protective_wings_are_further_otm():
    strikes=[23500,23800,24000,24200,24500,25000,25200]
    assert select_call_strike(strikes,24500,200)==25000
    assert select_put_strike(strikes,23500,200) is None

def test_lot_schedule():
    assert lot_size(date(2025,12,30))==75
    assert lot_size(date(2026,1,6))==65
