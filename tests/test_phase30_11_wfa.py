from research.phase30_11_wfa import FOLDS


def test_three_rolling_folds_are_non_overlapping_oos_and_hold_out_tail():
    assert list(FOLDS) == [1, 2, 3]
    assert FOLDS[1]["train"] == ("2025-09-01", "2026-01-18")
    assert FOLDS[1]["oos"] == ("2026-01-19", "2026-04-12")
    assert FOLDS[2]["train"] == ("2025-10-27", "2026-03-15")
    assert FOLDS[2]["oos"] == ("2026-03-16", "2026-06-07")
    assert FOLDS[3]["train"] == ("2025-12-22", "2026-05-24")
    assert FOLDS[3]["oos"] == ("2026-05-25", "2026-08-16")
