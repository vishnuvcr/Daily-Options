from pathlib import Path

from research.phase30_8_no_more_straddles_resolution import (
    VIDEO_ID,
    collect_primary_evidence,
    summarize,
)


def test_candidate_is_present_and_blocked_before_pnl():
    root = Path(__file__).resolve().parents[1]
    record = collect_primary_evidence(root)
    assert record["video_id"] == VIDEO_ID
    summary = summarize(record)
    assert summary["resolution_state"] == "BLOCKED_FOR_PNL"
    assert summary["no_pnl_authorization"] is True


def test_source_evidence_captures_known_fields():
    root = Path(__file__).resolve().parents[1]
    record = collect_primary_evidence(root)
    fields = record["source_fields"]
    assert fields["underlying"]
    assert fields["entry_action"]
    assert fields["strike_reference_full"]
    assert fields["width_reference"]
    assert fields["time_reference"]


def test_output_schema_keeps_essential_fields_unresolved():
    root = Path(__file__).resolve().parents[1]
    summary = summarize(collect_primary_evidence(root))
    assert "expiry_reference" in summary["unresolved_fields"]
    assert "stop_reference" in summary["unresolved_fields"]
    assert "target_reference" in summary["unresolved_fields"]
