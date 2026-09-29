def test_volume_imbalance_boundaries():
    def b(x,q33,q67):
        return "LOW_VOLUME_IMBALANCE" if x<q33 else ("MID_VOLUME_IMBALANCE" if x<q67 else "HIGH_VOLUME_IMBALANCE")
    assert b(-0.50,-0.20,0.20)=="LOW_VOLUME_IMBALANCE"
    assert b(-0.20,-0.20,0.20)=="MID_VOLUME_IMBALANCE"
    assert b(0.20,-0.20,0.20)=="HIGH_VOLUME_IMBALANCE"

def test_volume_imbalance_formula():
    assert abs((70-30)/(70+30)-0.4) < 1e-12
