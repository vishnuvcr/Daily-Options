#!/usr/bin/env python3
"""Deterministic Python archive for the Equity Income YouTube channel.

The repository is public, so the default mode encrypts transcript text before it
is committed. Plaintext can be written to a private/local directory instead.
No LLM is used for discovery or transcript retrieval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi

CHANNEL = "https://www.youtube.com/@equityincome"
SURFACES = (
    "https://www.youtube.com/@equityincome/videos",
    "https://www.youtube.com/@equityincome/shorts",
    "https://www.youtube.com/@equityincome/streams",
)
PREFERRED_LANGS = ("en", "en-IN", "hi")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_snippets(items) -> list[dict]:
    output = []
    previous = None
    for item in items:
        if isinstance(item, dict):
            text = clean_text(item.get("text", ""))
            start = float(item.get("start", 0))
            duration = float(item.get("duration", 0))
        else:
            text = clean_text(getattr(item, "text", ""))
            start = float(getattr(item, "start", 0))
            duration = float(getattr(item, "duration", 0))
        if not text:
            continue
        key = (round(start, 3), text)
        if key == previous:
            continue
        previous = key
        output.append({
            "start": round(start, 3),
            "duration": round(duration, 3),
            "text": text,
        })
    return output


def parse_vtt_timestamp(value: str) -> float:
    value = value.replace(",", ".")
    parts = value.split(":")
    if len(parts) == 2:
        mm, ss = parts
        return float(mm) * 60 + float(ss)
    hh, mm, ss = parts
    return float(hh) * 3600 + float(mm) * 60 + float(ss)


def parse_vtt(vtt: str) -> list[dict]:
    lines = [line.rstrip() for line in vtt.splitlines()]
    out = []
    i = 0
    while i < len(lines):
        if "-->" not in lines[i]:
            i += 1
            continue
        left, right = [x.strip() for x in lines[i].split("-->", 1)]
        try:
            start = parse_vtt_timestamp(left)
            stop = parse_vtt_timestamp(right.split()[0])
        except ValueError:
            i += 1
            continue
        i += 1
        parts = []
        while i < len(lines) and lines[i].strip():
            parts.append(re.sub(r"<[^>]+>", "", lines[i].strip()))
            i += 1
        text = clean_text(" ".join(parts))
        if text:
            out.append({
                "start": start,
                "duration": max(0.0, stop - start),
                "text": text,
            })
    return normalize_snippets(out)


def select_track(transcript_list):
    tracks = list(transcript_list)
    ordered = []
    for generated in (False, True):
        for lang in PREFERRED_LANGS:
            ordered.extend(
                t for t in tracks
                if bool(t.is_generated) == generated and t.language_code == lang
            )
    if ordered:
        return ordered[0]
    tracks.sort(key=lambda t: (bool(t.is_generated), t.language_code, t.language))
    return tracks[0] if tracks else None


def fetch_transcript(video_id: str, video_url: str, retries: int = 3):
    api = YouTubeTranscriptApi()
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            track = select_track(api.list(video_id))
            if track is None:
                raise RuntimeError("NO_TRANSCRIPT")
            fetched = track.fetch()
            snippets = normalize_snippets(fetched)
            if not snippets:
                raise RuntimeError("EMPTY_TRANSCRIPT")
            return snippets, track.language_code, track.language, bool(track.is_generated), "youtube-transcript-api"
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt * 2)

    # Fallback: obtain a subtitle track directly from yt-dlp.
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "socket_timeout": 15,
        "retries": 2,
        # Prefer clients that currently do not require YouTube PO tokens
        # for the relevant request classes when yt-dlp falls back to captions.
        "extractor_args": {
            "youtube": {
                "player_client": ["tv_simply", "web_embedded"],
            }
        },
    }
    for attempt in range(1, retries + 1):
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                candidates = []
                for field, generated in (("subtitles", False), ("automatic_captions", True)):
                    for lang, tracks in (info.get(field) or {}).items():
                        for track in tracks:
                            rank_lang = PREFERRED_LANGS.index(lang) if lang in PREFERRED_LANGS else 99
                            rank_ext = 0 if track.get("ext") == "vtt" else 1
                            candidates.append((int(generated), rank_lang, rank_ext, lang, generated, track))
                if not candidates:
                    raise RuntimeError(f"NO_SUBTITLE_FALLBACK: {last_error}")
                candidates.sort()
                _, _, _, lang, generated, track = candidates[0]
                raw = ydl.urlopen(track["url"]).read().decode("utf-8", errors="replace")
                snippets = parse_vtt(raw)
                if not snippets:
                    raise RuntimeError("EMPTY_VTT")
                return snippets, lang, lang, bool(generated), "yt-dlp-subtitles"
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt * 2)

    raise RuntimeError(f"TRANSCRIPT_FETCH_FAILED: {last_error}") from last_error


def discover() -> dict[str, dict]:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "ignoreerrors": True,
        "socket_timeout": 30,
        "retries": 3,
    }
    found: dict[str, dict] = {}
    with YoutubeDL(opts) as ydl:
        for surface in SURFACES:
            info = ydl.extract_info(surface, download=False) or {}
            for entry in info.get("entries") or []:
                if not entry:
                    continue
                video_id = entry.get("id")
                if not video_id:
                    continue
                found.setdefault(video_id, {
                    "video_id": video_id,
                    "webpage_url": entry.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}",
                    "title": entry.get("title"),
                    "playlist_sources": [],
                })
                if surface not in found[video_id]["playlist_sources"]:
                    found[video_id]["playlist_sources"].append(surface)
    return found


def enrich(video: dict) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "socket_timeout": 30,
        "retries": 3,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(video["webpage_url"], download=False)
    return {
        "video_id": info.get("id"),
        "title": info.get("title"),
        "webpage_url": info.get("webpage_url") or video["webpage_url"],
        "upload_date": info.get("upload_date"),
        "timestamp": info.get("timestamp"),
        "duration": info.get("duration"),
        "channel": info.get("channel"),
        "channel_id": info.get("channel_id"),
        "description": info.get("description") or "",
        "categories": info.get("categories") or [],
        "tags": info.get("tags") or [],
        "availability": info.get("availability"),
        "live_status": info.get("live_status"),
        "playlist_sources": sorted(video.get("playlist_sources", [])),
        "harvested_at_utc": now_utc(),
    }


def read_jsonl(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            out[str(item["video_id"])] = item
    return out


def write_jsonl(path: Path, records: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as fh:
        for video_id in sorted(records):
            fh.write(json.dumps(records[video_id], ensure_ascii=False, sort_keys=True) + "\n")
    temp.replace(path)


def payload(video_id: str, lang_code: str, lang: str, generated: bool,
            method: str, snippets: list[dict]) -> bytes:
    body = {
        "schema_version": 1,
        "video_id": video_id,
        "language_code": lang_code,
        "language": lang,
        "is_generated": generated,
        "method": method,
        "fetched_at_utc": now_utc(),
        "snippets": snippets,
    }
    return (json.dumps(body, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def archive_video(video: dict, transcript_root: Path,
                  plaintext_root: Path | None, key: str | None,
                  force: bool) -> dict:
    video_id = video["video_id"]
    encrypted_path = transcript_root / f"{video_id}.json.fernet"
    if encrypted_path.exists() and not force:
        return {
            "video_id": video_id,
            "status": "already_archived",
            "archive_path": str(encrypted_path.relative_to(transcript_root.parent)),
        }

    snippets, lang_code, lang, generated, method = fetch_transcript(
        video_id, video["webpage_url"]
    )
    plain = payload(video_id, lang_code, lang, generated, method, snippets)
    plain_hash = sha256_bytes(plain)

    if plaintext_root is not None:
        plaintext_root.mkdir(parents=True, exist_ok=True)
        (plaintext_root / f"{video_id}.json").write_bytes(plain)

    result = {
        "video_id": video_id,
        "status": "archived",
        "language_code": lang_code,
        "language": lang,
        "is_generated": generated,
        "method": method,
        "snippet_count": len(snippets),
        "plaintext_sha256": plain_hash,
        "fetched_at_utc": now_utc(),
    }

    if key:
        encrypted = Fernet(key.encode("ascii")).encrypt(plain)
        transcript_root.mkdir(parents=True, exist_ok=True)
        encrypted_path.write_bytes(encrypted)
        result["ciphertext_sha256"] = sha256_bytes(encrypted)
        result["archive_path"] = str(encrypted_path.relative_to(transcript_root.parent))
    else:
        result["ciphertext_sha256"] = None
        result["archive_path"] = str((plaintext_root / f"{video_id}.json").relative_to(transcript_root.parent))

    return result


def validate(records: dict[str, dict], root: Path, key: str | None) -> tuple[int, int]:
    checked = ok = 0
    for record in records.values():
        if record.get("status") not in {"archived", "already_archived"}:
            continue
        checked += 1
        p = root / record["archive_path"]
        if not p.exists():
            continue
        try:
            blob = p.read_bytes()
            if key:
                plain = Fernet(key.encode("ascii")).decrypt(blob)
                if sha256_bytes(plain) != record["plaintext_sha256"]:
                    continue
                if sha256_bytes(blob) != record["ciphertext_sha256"]:
                    continue
            else:
                if sha256_bytes(blob) != record["plaintext_sha256"]:
                    continue
            ok += 1
        except (InvalidToken, OSError, ValueError):
            continue
    return checked, ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel-url", default=CHANNEL)
    parser.add_argument("--output-root", type=Path, default=Path("data/equity_income"))
    parser.add_argument("--mode", choices=("encrypted", "private"), default="encrypted")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    key = os.environ.get("EQUITY_INCOME_ARCHIVE_KEY")
    if args.mode == "encrypted" and not key:
        raise SystemExit("EQUITY_INCOME_ARCHIVE_KEY is required for encrypted mode")

    root = args.output_root
    encrypted_root = root / "transcripts_encrypted"
    private_root = root / "transcripts_private" if args.mode == "private" else None
    video_manifest_path = root / "video_manifest.jsonl"
    transcript_manifest_path = root / "transcript_manifest.jsonl"
    error_path = root / "archive_errors.jsonl"

    videos = discover()
    logging.info("Discovered %d unique public videos", len(videos))
    if args.limit:
        videos = dict(sorted(videos.items())[:args.limit])

    video_manifest = read_jsonl(video_manifest_path)
    transcript_manifest = read_jsonl(transcript_manifest_path)
    errors = {}

    for index, video in enumerate(videos.values(), 1):
        vid = video["video_id"]
        logging.info("[%d/%d] %s", index, len(videos), vid)
        try:
            video_manifest[vid] = enrich(video)
        except Exception as exc:
            video_manifest[vid] = {
                **video,
                "metadata_error": repr(exc),
                "harvested_at_utc": now_utc(),
            }
            continue

        if transcript_manifest.get(vid, {}).get("status") in {"archived", "already_archived"} and not args.force:
            continue

        try:
            record = archive_video(
                video_manifest[vid],
                encrypted_root,
                private_root,
                key if args.mode == "encrypted" else None,
                args.force,
            )
            transcript_manifest[vid] = record
        except Exception as exc:
            transcript_manifest[vid] = {
                "video_id": vid,
                "status": "error",
                "error": repr(exc),
                "failed_at_utc": now_utc(),
            }
            errors[vid] = transcript_manifest[vid]

        write_jsonl(video_manifest_path, video_manifest)
        write_jsonl(transcript_manifest_path, transcript_manifest)
        time.sleep(0.5)

    checked, ok = validate(transcript_manifest, root, key if args.mode == "encrypted" else None)
    snapshot = {
        "schema_version": 1,
        "channel_url": args.channel_url,
        "channel_id": "UCxMt2GgYbO6-FCf0p4sAT0A",
        "harvested_at_utc": now_utc(),
        "discovered_videos": len(videos),
        "metadata_records": len(video_manifest),
        "transcript_archived": sum(x.get("status") in {"archived", "already_archived"} for x in transcript_manifest.values()),
        "transcript_errors": sum(x.get("status") == "error" for x in transcript_manifest.values()),
        "integrity_checked": checked,
        "integrity_ok": ok,
        "mode": args.mode,
        "tooling": {
            "yt-dlp": "2026.8.19",
            "youtube-transcript-api": "1.2.4",
            "cryptography": "50.0.1",
        },
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "channel_snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if errors:
        write_jsonl(error_path, errors)

    errors_count = sum(x.get("status") == "error" for x in transcript_manifest.values())
    metadata_errors = sum("metadata_error" in x for x in video_manifest.values())
    if checked != ok or errors_count or metadata_errors or len(video_manifest) != len(videos):
        logging.error("Archive incomplete: integrity=%d/%d transcript_errors=%d metadata_errors=%d metadata_records=%d discovered=%d", ok, checked, errors_count, metadata_errors, len(video_manifest), len(videos))
        return 2
    logging.info("Archive complete: %d videos; %d transcripts verified", len(videos), ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
