from pathlib import Path
from research.phase23_equity_income_catalog import validate

def test_catalog_exists_and_validates():
    assert Path("docs/equity_income_channel_catalog.md").exists()
    validate()
