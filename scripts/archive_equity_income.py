#!/usr/bin/env python3
"""Deterministic Python archive for the Equity Income YouTube channel.

The repository is public, so the default mode encrypts transcript text before it
is committed. Plaintext can be written to a private/local directory instead.
No LLM is used for discovery or transcript retrieval.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import os
import re
import sys
import requests
import time
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from yt_dlp import YoutubeDL
from yt_dlp.extractor.youtube._base import INNERTUBE_CLIENTS
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
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


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


def parse_innertube_json3(data: dict) -> list[dict]:
    out = []
    for event in data.get("events") or []:
        if not isinstance(event, dict) or not event.get("segs"):
            continue
        text_parts = []
        for seg in event.get("segs") or []:
            if isinstance(seg, dict) and seg.get("utf8"):
                text_parts.append(seg["utf8"])
        text = "".join(text_parts).strip()
        if not text:
            continue
        start = float(event.get("tStartMs", 0)) / 1000.0
        duration = float(event.get("dDurationMs", 0)) / 1000.0
        out.append({"start": start, "duration": duration, "text": text})
    return normalize_snippets(out)


def fetch_innertube(video_id: str) -> tuple[list[dict], str, bool] | None:
    """Use yt-dlp's pinned client definitions to ask YouTube for caption tracks.

    TV/embedded clients avoid the web client's current subtitle PO-token path.
    The returned caption track contains a server-signed base URL; no transcript
    text is inferred or generated locally.
    """
    session = requests.Session()
    for client_name in ("tv", "tv_downgraded", "web_embedded"):
        cfg = INNERTUBE_CLIENTS.get(client_name)
        if not cfg:
            continue
        ctx = json.loads(json.dumps(cfg["INNERTUBE_CONTEXT"]))
        client = ctx.setdefault("client", {})
        client.setdefault("hl", "en")
        client_name_header = str(cfg.get("INNERTUBE_CONTEXT_CLIENT_NAME", ""))
        client_version = str(client.get("clientVersion", ""))
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://www.youtube.com",
            "User-Agent": client.get("userAgent") or "Mozilla/5.0",
            "X-YouTube-Client-Name": client_name_header,
            "X-YouTube-Client-Version": client_version,
        }
        body = {
            "context": ctx,
            "videoId": video_id,
            "contentCheckOk": True,
            "racyCheckOk": True,
        }
        try:
            response = session.post(
                "https://www.youtube.com/youtubei/v1/player",
                params={"prettyPrint": "false"},
                json=body,
                headers=headers,
                timeout=(3, 8),
            )
            if response.status_code != 200:
                continue
            data = response.json()
            tracks = (
                data.get("captions", {})
                .get("playerCaptionsTracklistRenderer", {})
                .get("captionTracks", [])
            )
            ranked = []
            for track in tracks or []:
                lang = track.get("languageCode", "")
                generated = track.get("kind") == "asr"
                rank_lang = PREFERRED_LANGS.index(lang) if lang in PREFERRED_LANGS else 99
                ranked.append((int(generated), rank_lang, lang, generated, track))
            ranked.sort()
            for _, _, lang, generated, track in ranked:
                base_url = track.get("baseUrl")
                if not base_url:
                    continue
                cap = session.get(
                    base_url,
                    params={"fmt": "json3"},
                    headers={"User-Agent": headers["User-Agent"]},
                    timeout=(3, 8),
                )
                if cap.status_code != 200 or not cap.text.strip():
                    continue
                try:
                    snippets = parse_innertube_json3(cap.json())
                except (ValueError, TypeError):
                    snippets = []
                if snippets:
                    return snippets, lang, generated
        except (requests.RequestException, ValueError, KeyError, TypeError):
            continue
    return None


def fetch_timedtext(video_id: str) -> tuple[list[dict], str, bool] | None:
    """Try direct caption retrieval with short bounded HTTP requests."""
    endpoint = "https://www.youtube.com/api/timedtext"
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}
    candidates = (
        ("en", True),   # generated English
        ("en", False),  # manual English
        ("hi", True),   # generated Hindi
    )
    for lang, generated in candidates:
        params = {"v": video_id, "lang": lang, "fmt": "vtt"}
        if generated:
            params["kind"] = "asr"
        try:
            response = session.get(
                endpoint, params=params, headers=headers, timeout=(3, 5)
            )
            if response.status_code != 200 or not response.text.strip():
                continue
            snippets = parse_vtt(response.text)
            if snippets:
                return snippets, lang, generated
        except requests.RequestException:
            continue
    return None


def select_track(transcript_list):
    tracks = list(transcript_list)
    ordered = []
    for generated in (False, True):
        for lang in PREFERRED_LANGS:
            ordered.extend(
                t for t in tracks
                if bool(getattr(t, "is_generated", False)) == generated
                and getattr(t, "language_code", "") == lang
            )
    if ordered:
        return ordered[0]
    tracks.sort(
        key=lambda t: (
            bool(getattr(t, "is_generated", False)),
            getattr(t, "language_code", ""),
            getattr(t, "language", ""),
        )
    )
    return tracks[0] if tracks else None


def parse_timestamped_markdown(text: str) -> list[dict]:
    """Parse the timestamped Markdown format used by the no-key fallback service."""
    out = []
    stamp = re.compile(r"^\[(\d{1,3}):(\d{2})(?::(\d{2}))?\]\s*(.+?)\s*$")
    for line in text.splitlines():
        match = stamp.match(line.strip())
        if not match:
            continue
        first, second, third, caption = match.groups()
        if third is None:
            start = int(first) * 60 + int(second)
        else:
            start = int(first) * 3600 + int(second) * 60 + int(third)
        caption = clean_text(caption)
        if caption:
            out.append({"start": float(start), "duration": 0.0, "text": caption})
    return normalize_snippets(out)


def fetch_youtube_transcript_api(video_id: str):
    """Use the source-caption Python API as a separate first-party extraction path."""
    try:
        api = YouTubeTranscriptApi()
        tracks = list(api.list(video_id))
        ranked = []
        for track in tracks:
            language_code = getattr(track, "language_code", "")
            language = getattr(track, "language", language_code)
            generated = bool(getattr(track, "is_generated", False))
            lang_rank = PREFERRED_LANGS.index(language_code) if language_code in PREFERRED_LANGS else 99
            ranked.append((int(generated), lang_rank, language_code, track))
        ranked.sort()
        for _, _, language_code, track in ranked:
            try:
                fetched = track.fetch()
                raw = fetched.to_raw_data() if hasattr(fetched, "to_raw_data") else list(fetched)
                snippets = normalize_snippets(raw)
                if snippets:
                    return (
                        snippets,
                        language_code,
                        getattr(track, "language", language_code),
                        bool(getattr(track, "is_generated", False)),
                        "youtube-transcript-api",
                    )
            except Exception:
                continue
        raise RuntimeError("NO_USABLE_TRANSCRIPT_API_TRACK")
    except Exception as exc:
        return None, repr(exc)


def fetch_ytdlp_subtitles(video_url: str):
    """Try yt-dlp caption extraction across clients with different current YouTube rules."""
    profiles = (
        ("web", True),
        ("mweb", True),
        ("tv", False),
        ("web_embedded", False),
        ("android_vr", False),
    )
    errors = []
    for client_name, use_pot_provider in profiles:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "socket_timeout": 12,
            "retries": 1,
            "extractor_args": {
                "youtube": {
                    "player_client": [client_name],
                },
            },
        }
        if use_pot_provider:
            opts["extractor_args"]["youtubepot-bgutilhttp"] = {
                "base_url": ["http://127.0.0.1:4416"],
            }
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
                candidates.sort()
                for _, _, _, lang, generated, track in candidates:
                    url = track.get("url")
                    if not url:
                        continue
                    raw = ydl.urlopen(url).read().decode("utf-8", errors="replace")
                    snippets = parse_vtt(raw)
                    if snippets:
                        return snippets, lang, lang, bool(generated), f"yt-dlp-subtitles:{client_name}"
                raise RuntimeError("NO_USABLE_YTDLP_SUBTITLE")
        except Exception as exc:
            errors.append(f"{client_name}:{exc!r}")
    return None, errors


def fetch_external_transcript_service(video_id: str):
    """Last-resort caption proxy; preserves service provenance and does not generate text locally."""
    from urllib.parse import quote

    endpoints = (
        "https://youtube-transcript.ai/transcript/{video_id}.txt?lang=en",
        "https://youtube-transcript.ai/transcript/{video_id}.txt?lang=hi",
        "https://youtube-transcript.ai/transcript/{video_id}.txt",
    )
    errors = []
    headers = {"User-Agent": "Daily-Options-Equity-Income-Archive/1.0"}
    for template in endpoints:
        url = template.format(video_id=quote(video_id, safe=""))
        try:
            response = requests.get(url, headers=headers, timeout=(5, 15))
            if response.status_code != 200 or not response.text.strip():
                errors.append(f"{response.status_code}:{url}")
                continue
            snippets = parse_timestamped_markdown(response.text)
            if not snippets:
                errors.append(f"NO_TIMESTAMPS:{url}")
                continue
            lang_match = re.search(r"^Language:\s*([^\s·]+)", response.text, flags=re.MULTILINE)
            lang_code = lang_match.group(1) if lang_match else "en"
            return snippets, lang_code, lang_code, None, "youtube-transcript-ai"
        except requests.RequestException as exc:
            errors.append(repr(exc))
    return None, errors


def fetch_transcript(video_id: str, video_url: str, retries: int = 1):
    """Retrieve a source transcript with bounded, provenance-preserving Python fallbacks.

    No transcript text is generated by an LLM. The order is:
    1) yt-dlp subtitle extraction with several YouTube player clients,
    2) youtube-transcript-api,
    3) direct InnerTube caption tracks,
    4) direct timedtext,
    5) no-key third-party transcript proxy as a last resort.
    """
    ytdlp_result = fetch_ytdlp_subtitles(video_url)
    if ytdlp_result[0] is not None:
        return ytdlp_result
    errors = [f"yt-dlp:{err}" for err in ytdlp_result[1]]

    api_result = fetch_youtube_transcript_api(video_id)
    if api_result[0] is not None:
        return api_result
    errors.append(f"youtube-transcript-api:{api_result[1]}")

    timed = fetch_innertube(video_id)
    if timed is not None:
        snippets, lang, generated = timed
        return snippets, lang, lang, generated, "youtube-innertube"

    timed = fetch_timedtext(video_id)
    if timed is not None:
        snippets, lang, generated = timed
        return snippets, lang, lang, generated, "youtube-timedtext"

    external = fetch_external_transcript_service(video_id)
    if external[0] is not None:
        return external

    errors.append(f"youtube-transcript-ai:{external[1]}")
    detail = " | ".join(errors[-12:])
    raise RuntimeError(f"TRANSCRIPT_FETCH_FAILED: {detail}")


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


def payload(video_id: str, lang_code: str, lang: str, generated: bool | None,
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
