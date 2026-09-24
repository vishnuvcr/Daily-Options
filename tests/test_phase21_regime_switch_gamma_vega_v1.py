from research.phase21_regime_switch_gamma_vega_v1 import variants


def test_phase21_grid():
    v = variants()
    assert len(v) == 60
    assert {x['regime'] for x in v} == {'EXPANSION', 'CALM'}
