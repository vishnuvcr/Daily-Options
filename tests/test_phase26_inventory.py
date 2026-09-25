from pathlib import Path
import json

from scripts.build_equity_income_inventory import family_guess, normalize_title


def test_family_guess_is_deterministic():
    assert "iron_condor" in family_guess("Iron Condor Super Adjustments")
    assert "calendar" in family_guess("Weekly Cross Calendar | Hedged Strategy")


def test_normalize_title_stable():
    assert normalize_title("  Set & Strike!!! ") == "set strike"


def test_inventory_fixture_schema(tmp_path: Path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "video_manifest.jsonl").write_text(
        json.dumps({
            "video_id": "abc123",
            "title": "Iron Fly Strategy",
            "webpage_url": "https://www.youtube.com/watch?v=abc123",
        }) + "\n",
        encoding="utf-8",
    )
    (root / "transcript_manifest.jsonl").write_text(
        json.dumps({"video_id": "abc123", "status": "archived", "method": "youtubegpt-json", "snippet_count": 5}) + "\n",
        encoding="utf-8",
    )

    from scripts.build_equity_income_inventory import main
    import sys
    old = sys.argv[:]
    try:
        sys.argv = ["build", "--root", str(root)]
        assert main() == 0
    finally:
        sys.argv = old

    snapshot = json.loads((root / "inventory_snapshot.json").read_text(encoding="utf-8"))
    assert snapshot["videos"] == 1
    assert snapshot["transcript_status_counts"]["archived"] == 1
    assert snapshot["transcript_verified"] == 1



def test_complete_archive_gate():
    videos = [{"video_id": "a", "title": "Iron Condor Strategy"}]
    tx = [{"video_id": "a", "status": "archived", "method": "youtubegpt-json", "snippet_count": 4}]
    rows = build_rows(videos, tx)
    assert len(rows) == 1
    assert rows[0]["transcript_integrity"] == "VERIFIED"
    assert rows[0]["source_fidelity"] == "UNRESOLVED"
