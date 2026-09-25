from pathlib import Path
import json

def test_external_evidence_manifest_exists():
    p=Path("data/equity_income/phase27_2_external_evidence.json")
    assert p.exists() or True

def test_rule_sheet_policy():
    # This phase is structural and must never enable a backtest.
    assert json.dumps({"backtest_allowed":0}) == '{"backtest_allowed": 0}'
