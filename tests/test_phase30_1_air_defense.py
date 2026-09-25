import math
import pandas as pd
from datetime import date
from research.phase30_1_air_defense import expected_move, select_call_strike, select_put_strike, lot_size, previous_vix

def test_expected_move():
    got=expected_move(24000.0,18.0,5*24*60,1.0)
    expected=24000.0*0.18*math.sqrt((5*24*60)/(365*24*60))
    assert abs(got-expected)<1e-9

def test_strike_selection():
    strikes=[23500,23800,24000,24200,24500,25000]
    assert select_call_strike(strikes,24000,450)==24500
    assert select_put_strike(strikes,24000,450)==23500

def test_lot_schedule():
    assert lot_size(date(2025,12,30))==75
    assert lot_size(date(2026,1,6))==65

def test_previous_vix_is_strictly_prior_day():
    v=pd.DataFrame({'date':[date(2025,9,1),date(2025,9,2)],'close':[14.0,15.0]})
    assert previous_vix(v,date(2025,9,2))==14.0
    assert previous_vix(v,date(2025,9,1)) is None
