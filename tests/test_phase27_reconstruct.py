from research.phase27_reconstruct import build_record, norm


def test_norm():
    assert norm("  NIFTY 50\n") == "nifty 50"


def test_build_record_marks_source_explicit_fields():
    video = {"video_id": "x", "title": "Iron Condor", "webpage_url": "https://youtube.com/watch?v=x"}
    data = {
        "segments": [
            {"start": 0, "dur": 1000, "text": "Enter on Wednesday at 9:20. Adjust on Thursday. Exit on Monday."},
            {"start": 1000, "dur": 1000, "text": "Use NIFTY and a 25 point premium. One strike OTM. Stop loss at 50 percent."},
        ]
    }
    r = build_record(video, data)
    assert r["field_status"]["entry_day"] == "SOURCE-EXPLICIT"
    assert r["field_status"]["adjustment_day"] == "SOURCE-EXPLICIT"
    assert r["field_status"]["exit_day"] == "SOURCE-EXPLICIT"
    assert r["field_status"]["underlying"] == "SOURCE-EXPLICIT"
    assert r["field_status"]["premium_zone"] == "SOURCE-EXPLICIT"
    assert r["field_status"]["strike_reference"] == "SOURCE-EXPLICIT"
    assert r["field_status"]["stop_reference"] == "SOURCE-EXPLICIT"
