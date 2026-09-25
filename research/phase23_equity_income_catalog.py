from __future__ import annotations
from pathlib import Path
import csv

CATALOG = Path("docs/equity_income_channel_catalog.md")

REQUIRED_HEADINGS = [
    "# Equity Income YouTube Strategy Catalogue",
    "## Observed strategy hypotheses",
    "## Sources",
    "## Evidence rule",
]

def validate() -> None:
    text = CATALOG.read_text(encoding="utf-8")
    for h in REQUIRED_HEADINGS:
        assert h in text, f"missing heading: {h}"
    assert "Air Defense" in text
    assert "Bear put spread" in text
    assert "Jade Lizard" in text
    assert "calendar" in text.lower()
    assert "diagonal" in text.lower()
    assert "Evidence rule" in text
    print("validated Equity Income strategy catalogue")

if __name__ == "__main__":
    validate()
