from research.phase29_4_iron_dome_rule_reconstruction import (
    extract_fact_candidates,
    classify_rule_status,
)


def test_fact_extraction_finds_source_anchors():
    snippets = [
        {"start": 10.0, "text": "60% mark Monday morning at 9:30"},
        {"start": 20.0, "text": "sell 23,900 and buy 200 points up and 200 points below"},
        {"start": 30.0, "text": "two, three, maybe four days"},
        {"start": 40.0, "text": "3:00 p.m. on the expiry day"},
    ]
    facts = extract_fact_candidates(snippets)
    assert 60 in facts["percentages"]
    assert "Monday" in facts["weekdays"]
    assert "09:30" in facts["times"]
    assert 23900 in facts["strike_like_values"]
    assert 200 in facts["point_values"]
    assert facts["hold_days"] == [2, 3, 4]
    assert "15:00" in facts["times"]


def test_rule_classification_is_conservative():
    assert classify_rule_status("explicit") == "EXPLICIT"
    assert classify_rule_status("example") == "ILLUSTRATIVE"
    assert classify_rule_status("formalization") == "FORMALIZATION_REQUIRED"
    assert classify_rule_status("unknown") == "UNRESOLVED"
