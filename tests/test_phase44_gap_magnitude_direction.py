def test_gap_bucket_thresholds():
    def bucket(x):
        a=abs(x)
        return 'SMALL_GAP' if a<0.005 else ('MEDIUM_GAP' if a<0.01 else 'LARGE_GAP')
    assert bucket(0.0049)=='SMALL_GAP'
    assert bucket(0.005)=='MEDIUM_GAP'
    assert bucket(0.0099)=='MEDIUM_GAP'
    assert bucket(0.01)=='LARGE_GAP'
