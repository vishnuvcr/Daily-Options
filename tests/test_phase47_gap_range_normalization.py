def test_gap_range_buckets():
    def b(x):
        return "SMALL_REL_GAP" if x < 0.20 else ("MEDIUM_REL_GAP" if x < 0.40 else "LARGE_REL_GAP")
    assert b(0.10)=="SMALL_REL_GAP"
    assert b(0.20)=="MEDIUM_REL_GAP"
    assert b(0.39)=="MEDIUM_REL_GAP"
    assert b(0.40)=="LARGE_REL_GAP"
