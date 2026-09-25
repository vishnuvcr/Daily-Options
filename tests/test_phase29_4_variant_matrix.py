from research.phase29_4_variant_matrix import ADJUST, ENTRY, EXIT, TRIGGER


def test_variant_dimensions_are_preregistered():
    assert len(ENTRY) == 3
    assert len(TRIGGER) == 2
    assert len(ADJUST) == 3
    assert len(EXIT) == 2


def test_matrix_product_size():
    assert len(ENTRY) * len(TRIGGER) * len(ADJUST) * len(EXIT) == 36
