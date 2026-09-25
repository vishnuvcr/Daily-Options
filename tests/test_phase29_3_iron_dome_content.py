import re

from research.phase29_3_iron_dome_content import expiry_date, norm_text


def test_norm_text():
    assert norm_text(" a   b\n c ") == "a b c"


def test_expiry_date():
    assert expiry_date("options/NIFTY/2026-05-05.parquet").isoformat() == "2026-05-05"


def test_expiry_date_rejects_nonexpiry():
    assert expiry_date("options/NIFTY/README.md") is None
