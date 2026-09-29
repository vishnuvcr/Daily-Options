import pandas as pd
from datetime import date
from research.strategy_otm12_ratio_backspread import lot_size, pick_otm, cost

def test_otm_selection_is_first_and_second_listed_strikes():
    c = pd.DataFrame({"option_type":["CE","CE","CE","PE","PE","PE"],"strike":[100,110,120,100,90,80]})
    assert pick_otm(c, 105) == {"short_ce":110.0,"long_ce":120.0,"short_pe":100.0,"long_pe":90.0}

def test_lot_size_regimes_match_repository_convention():
    assert lot_size(date(2021,7,1)) == 50
    assert lot_size(date(2024,4,25)) == 50
    assert lot_size(date(2024,4,26)) == 25
    assert lot_size(date(2024,11,21)) == 75
    assert lot_size(date(2026,1,6)) == 65

def test_stress_slippage_cost_is_higher():
    legs=[{"entry":10.0,"exit":12.0,"qty":1,"sign":-1},{"entry":5.0,"exit":3.0,"qty":2,"sign":1},
          {"entry":10.0,"exit":12.0,"qty":1,"sign":-1},{"entry":5.0,"exit":3.0,"qty":2,"sign":1}]
    base=cost(legs,65,0.20,date(2026,1,10),date(2026,1,10))
    stress=cost(legs,65,0.40,date(2026,1,10),date(2026,1,10))
    assert stress > base
