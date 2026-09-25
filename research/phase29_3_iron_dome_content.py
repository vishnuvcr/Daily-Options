#!/usr/bin/env python3
"""Phase 29.3 deterministic transcript + contract-content inspection.

The script uses Python transcript retrieval, never a model-generated transcript.
It stores only hashes, timestamps, and short evidence snippets, not full
transcript plaintext.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

VIDEOS = [
    {
        "video_id": "5xz7X5QsFv8",
        "title": "Nifty Iron Dome - 2 Adjustments Only for Working People",
        "reference_date": "2026-04-30",
    },
    {
        "video_id": "9cetNfglyO4",
        "title": "Nifty Iron Dome Options Strategy - 2 Adjustments Only for Working People",
        "reference_date": "2026-05-02",
    },
]
HF_REPO = "thetrademarkk/india-index-options-1m"
HF_REV = "51ca58c"
RISSIN_REPO = "rissin/nse-options-intraday"
RISSIN_REV = "78b1c5468255d18cf492984bfe6fe4e3ac874d7c"

RULE_TERMS = [
    "entry", "enter", "sell", "buy", "call", "put", "ce", "pe", "strike",
    "lot", "lots", "expiry", "expire", "adjust", "adjustment", "move",
    "shift", "hedge", "stop", "stoploss", "loss", "exit", "close",
    "square", "target", "profit", "ironfly", "iron fly", "dome",
]
NUMBER_PAT = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?(?![A-Za-z])")


def norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def transcript(video_id: str) -> dict:
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id, languages=["en"])
    snippets = []
    parts = []
    for s in fetched.snippets:
        txt = norm_text(s.text)
        parts.append(txt)
        snippets.append({"start": float(s.start), "duration": float(s.duration), "text": txt})
    full = " ".join(parts)
    sha = hashlib.sha256(full.encode("utf-8")).hexdigest()

    evidence = []
    for i, s in enumerate(snippets):
        lower = s["text"].lower()
        if any(term in lower for term in RULE_TERMS) or NUMBER_PAT.search(s["text"]):
            context = " ".join(x["text"] for x in snippets[max(0, i - 1): min(len(snippets), i + 2)])
            evidence.append({
                "start": s["start"],
                "text": norm_text(context)[:320],
                "trigger_terms": sorted({term for term in RULE_TERMS if term in lower})[:8],
            })
    return {
        "status": "OK",
        "video_id": video_id,
        "sha256": sha,
        "snippet_count": len(snippets),
        "evidence_count": len(evidence),
        "evidence": evidence[:160],
        "language": getattr(fetched, "language_code", "en"),
    }


def list_expiry_files() -> list[str]:
    api = HfApi()
    files = []
    for item in api.list_repo_tree(
        repo_id=HF_REPO,
        path_in_repo="options/NIFTY",
        recursive=True,
        expand=False,
        revision=HF_REV,
        repo_type="dataset",
        token=False,
    ):
        path = getattr(item, "path", "")
        if path.lower().endswith(".parquet"):
            files.append(path)
    return sorted(files)


def expiry_date(path: str) -> date | None:
    m = re.search(r"/(\d{4}-\d{2}-\d{2})\.parquet$", path)
    return date.fromisoformat(m.group(1)) if m else None


def bounded_expiry_inventory(files: list[str]) -> list[dict]:
    out = []
    for v in VIDEOS:
        ref = date.fromisoformat(v["reference_date"])
        candidates = []
        for path in files:
            d = expiry_date(path)
            if d and ref - timedelta(days=3) <= d <= ref + timedelta(days=21):
                candidates.append({"path": path, "expiry": d.isoformat()})
        out.append({
            "video_id": v["video_id"],
            "reference_date": v["reference_date"],
            "candidate_expiry_files": candidates,
        })
    return out


def inspect_one(path: str) -> dict:
    """Download only the selected expiry Parquet and inspect schema/metadata."""
    try:
        local = hf_hub_download(
            repo_id=HF_REPO,
            filename=path,
            revision=HF_REV,
            repo_type="dataset",
            cache_dir=".hf_cache",
        )
        import pyarrow.parquet as pq

        pf = pq.ParquetFile(local)
        schema = [str(x) for x in pf.schema.names]
        required = [x for x in ["timestamp", "strike", "option_type", "expiry", "open", "high", "low", "close", "volume"] if x in schema]
        sample = {}
        if required:
            table = pf.read_row_group(0, columns=required)
            for col in required:
                vals = table[col].to_pylist()[:50]
                sample[col] = vals[:10]
        return {
            "status": "OK",
            "path": path,
            "row_groups": pf.num_row_groups,
            "schema": schema,
            "required_columns_present": required,
            "row_group0_sample": sample,
        }
    except Exception as exc:
        return {"status": "ERROR", "path": path, "error": str(exc)}


def main() -> int:
    outdir = Path("reports")
    outdir.mkdir(parents=True, exist_ok=True)
    Path(".hf_cache").mkdir(exist_ok=True)

    transcript_rows = []
    for v in VIDEOS:
        try:
            transcript_rows.append(transcript(v["video_id"]))
        except Exception as exc:
            transcript_rows.append({
                "status": "ERROR",
                "video_id": v["video_id"],
                "error": str(exc),
            })

    archive_manifest = {
        "tool": "youtube-transcript-api",
        "videos": transcript_rows,
        "plaintext_persisted": False,
    }
    Path("data/equity_income/phase29_3_transcript_fetch_manifest.json").write_text(
        json.dumps(archive_manifest, indent=2) + "\n", encoding="utf-8"
    )
    Path("reports/phase29_3_iron_dome_rule_evidence.json").write_text(
        json.dumps({"videos": transcript_rows}, indent=2) + "\n", encoding="utf-8"
    )

    files = list_expiry_files()
    inv = bounded_expiry_inventory(files)
    Path("reports/phase29_3_expiry_file_inventory.json").write_text(
        json.dumps({
            "repo": HF_REPO,
            "revision": HF_REV,
            "total_nifty_expiry_parquet_files": len(files),
            "candidate_files": inv,
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    content_checks = []
    for item in inv:
        for cand in item["candidate_expiry_files"]:
            content_checks.append(inspect_one(cand["path"]))

    transcript_ok = sum(x["status"] == "OK" for x in transcript_rows)
    transcript_blocked = sum(x["status"] != "OK" for x in transcript_rows)
    content_ok = sum(x["status"] == "OK" for x in content_checks)

    summary = {
        "phase": "29.3",
        "candidate_videos": len(VIDEOS),
        "transcript_fetch_ok": transcript_ok,
        "transcript_fetch_blocked": transcript_blocked,
        "nifty_expiry_parquet_files_at_pin": len(files),
        "candidate_expiry_files_found": sum(len(x["candidate_expiry_files"]) for x in inv),
        "expiry_content_checks_ok": content_ok,
        "rule_status": "RECONSTRUCTION_REQUIRED" if transcript_blocked else "SOURCE_TEXT_FETCHED_PENDING_HUMAN_RULE_FREEZE",
        "numerical_backtest_allowed": 0,
        "phase30_gate": "BLOCKED",
        "next_required": [
            "Freeze deterministic leg/strike/adjustment/exit rules from transcript evidence.",
            "Join each required leg to historical contract data and dated NSE lot/expiry rules.",
            "Do not infer bid/ask from OHLC."
        ],
    }
    Path("reports/phase29_3_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
