import pandas as pd
from research.phase14_global_cross_market_opening_gap_later_oos_rissin import frozen_signal_dates

def test_frozen_rule():
    x=pd.DataFrame({'trade_date':[pd.Timestamp('2025-01-02').date()],
                    'datetime':pd.to_datetime(['2025-01-02 04:00:00']),
                    'trade_time_ist':['09:30:00'],
                    'global_global3':[1.0],
                    'gap_signal':[-0.01],
                    'spot_close':[100.0]})
    y=frozen_signal_dates(x)
    assert len(y)==1 and y.iloc[0].direction=='CALL'
