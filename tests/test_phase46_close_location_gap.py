def test_close_location_buckets():
    def b(x): return 'LOW_CLOSE' if x<0.33 else ('MID_CLOSE' if x<=0.67 else 'HIGH_CLOSE')
    assert b(0.2)=='LOW_CLOSE'; assert b(0.33)=='MID_CLOSE'; assert b(0.67)=='MID_CLOSE'; assert b(0.8)=='HIGH_CLOSE'
