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
        json.dumps({"video_id": "abc123", "status": "error", "error": "TEST"}) + "\n",
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
    assert snapshot["transcript_status_counts"]["error"] == 1
