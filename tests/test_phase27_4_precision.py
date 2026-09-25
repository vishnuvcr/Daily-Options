from research.phase27_4_precision import extract, status

def test_clock_not_ratio_or_lot():
    seg=[{"start":0,"text":"Enter at 3:30 and keep 5:3 ratio."}]
    f=extract(seg)
    assert any(x["value"]=="3:30" for x in f["time_reference"])
    assert any(x["value"]=="5:3" for x in f["ratio_reference"])
    assert not f["lot_reference"]

def test_zero_premium_filtered():
    seg=[{"start":0,"text":"premium 0 is not a valid credit reference; premium of 25 points."}]
    f=extract(seg)
    assert all(float(x["value"])>0 for x in f["premium_zone"])

def test_width_requires_width_context():
    seg=[{"start":0,"text":"250 points wide spread."},{"start":10,"text":"250 points move."}]
    f=extract(seg)
    assert any(x["value"]=="250" for x in f["width_reference"])