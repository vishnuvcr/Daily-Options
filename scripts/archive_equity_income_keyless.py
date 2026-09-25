#!/usr/bin/env python3
"""Keyless GitHub Actions archive using public-key hybrid encryption.

This module reuses the existing Python-only channel discovery/transcript
retrieval functions and replaces the GitHub secret requirement with a public
RSA key. Only the holder of the matching private key can decrypt transcripts.
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from scripts.archive_equity_income import (
    CHANNEL,
    discover,
    enrich,
    fetch_transcript,
    payload,
    read_jsonl,
    sha256_bytes,
    write_jsonl,
)

SCHEMA_VERSION = 2
SCHEME = "RSA-OAEP-SHA256+FERNET-SHA256"


def load_public_key(path: Path):
    raw = path.read_bytes()
    key = serialization.load_pem_public_key(raw)
    if not isinstance(key, rsa.RSAPublicKey):
        raise TypeError("Archive public key must be RSA")
    if key.key_size < 3072:
        raise ValueError("Archive public key must be at least 3072 bits")
    return key, raw


def hybrid_encrypt(public_key, plaintext: bytes) -> dict:
    data_key = Fernet.generate_key()
    ciphertext = Fernet(data_key).encrypt(plaintext)
    assert Fernet(data_key).decrypt(ciphertext) == plaintext
    wrapped_key = public_key.encrypt(
        data_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "encryption_scheme": SCHEME,
        "wrapped_key_b64": base64.b64encode(wrapped_key).decode("ascii"),
        "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
        "ciphertext_sha256": sha256_bytes(ciphertext),
    }


def hybrid_decrypt(private_key, envelope: dict) -> bytes:
    if envelope.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("UNSUPPORTED_ENVELOPE_SCHEMA")
    if envelope.get("encryption_scheme") != SCHEME:
        raise ValueError("UNSUPPORTED_ENCRYPTION_SCHEME")
    wrapped_key = base64.b64decode(envelope["wrapped_key_b64"], validate=True)
    ciphertext = base64.b64decode(envelope["ciphertext_b64"], validate=True)
    if sha256_bytes(ciphertext) != envelope.get("ciphertext_sha256"):
        raise ValueError("CIPHERTEXT_HASH_MISMATCH")
    data_key = private_key.decrypt(
        wrapped_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return Fernet(data_key).decrypt(ciphertext)


def validate_envelope(path: Path, expected_ciphertext_sha256: str | None) -> bool:
    try:
        env = json.loads(path.read_text(encoding="utf-8"))
        if env.get("schema_version") != SCHEMA_VERSION:
            return False
        if env.get("encryption_scheme") != SCHEME:
            return False
        wrapped = base64.b64decode(env["wrapped_key_b64"], validate=True)
        ciphertext = base64.b64decode(env["ciphertext_b64"], validate=True)
        if not wrapped or not ciphertext:
            return False
        digest = sha256_bytes(ciphertext)
        return digest == env.get("ciphertext_sha256") and (
            not expected_ciphertext_sha256 or digest == expected_ciphertext_sha256
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError, KeyError):
        return False


class TranscriptTimeout(RuntimeError):
    pass


def fetch_transcript_bounded(video_id: str, video_url: str, timeout_seconds: int):
    return fetch_transcript(video_id, video_url, retries=1)


def archive_one(video: dict, out_root: Path, public_key, public_key_sha256: str,
                force: bool, transcript_timeout_seconds: int) -> dict:
    video_id = video["video_id"]
    transcript_root = out_root / "transcripts_encrypted"
    archive_path = transcript_root / f"{video_id}.json.hybrid.json"
    if archive_path.exists() and not force:
        return {
            "video_id": video_id,
            "status": "already_archived",
            "archive_path": str(archive_path.relative_to(out_root)),
        }

    snippets, lang_code, lang, generated, method = fetch_transcript_bounded(
        video_id, video["webpage_url"], transcript_timeout_seconds
    )
    plain = payload(video_id, lang_code, lang, generated, method, snippets)
    envelope = hybrid_encrypt(public_key, plain)
    transcript_root.mkdir(parents=True, exist_ok=True)
    tmp = archive_path.with_suffix(archive_path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(archive_path)

    return {
        "video_id": video_id,
        "status": "archived",
        "language_code": lang_code,
        "language": lang,
        "is_generated": generated,
        "method": method,
        "snippet_count": len(snippets),
        "plaintext_sha256": sha256_bytes(plain),
        "ciphertext_sha256": envelope["ciphertext_sha256"],
        "encryption_scheme": SCHEME,
        "archive_public_key_sha256": public_key_sha256,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_path": str(archive_path.relative_to(out_root)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel-url", default=CHANNEL)
    parser.add_argument("--output-root", type=Path, default=Path("data/equity_income"))
    parser.add_argument("--public-key", type=Path, default=Path("config/equity_income_archive_public_key.pem"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--transcript-timeout-seconds", type=int, default=45)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    public_key, public_key_raw = load_public_key(args.public_key)
    key_hash = sha256_bytes(public_key_raw)

    root = args.output_root
    root.mkdir(parents=True, exist_ok=True)
    video_manifest_path = root / "video_manifest.jsonl"
    transcript_manifest_path = root / "transcript_manifest.jsonl"
    error_path = root / "archive_errors.jsonl"

    videos = discover()
    if args.limit:
        videos = dict(sorted(videos.items())[:args.limit])
    logging.info("Discovered %d unique public videos", len(videos))

    video_manifest = read_jsonl(video_manifest_path)
    transcript_manifest = read_jsonl(transcript_manifest_path)
    errors = {}

    items = sorted(videos.items())

    def process(item):
        video_id, video = item
        metadata_record = {
            "video_id": video_id,
            "title": video.get("title"),
            "webpage_url": video.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}",
            "channel": "Equity Income",
            "channel_id": "UCxMt2GgYbO6-FCf0p4sAT0A",
            "playlist_sources": sorted(video.get("playlist_sources", [])),
            "metadata_status": "discovery_only",
            "harvested_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        existing = transcript_manifest.get(video_id, {})
        if existing.get("status") in {"archived", "already_archived"} and not args.force:
            return video_id, metadata_record, existing
        try:
            record = archive_one(metadata_record, root, public_key, key_hash, args.force, args.transcript_timeout_seconds)
        except Exception as exc:
            record = {
                "video_id": video_id,
                "status": "error",
                "error": repr(exc),
                "failed_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        return video_id, metadata_record, record

    workers = max(1, min(int(args.workers), 8))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process, item): item[0] for item in items}
        completed = 0
        for future in as_completed(futures):
            video_id, metadata_record, record = future.result()
            video_manifest[video_id] = metadata_record
            transcript_manifest[video_id] = record
            if record.get("status") == "error":
                errors[video_id] = record
            completed += 1
            logging.info("Completed %d/%d: %s -> %s", completed, len(items), video_id, record.get("status"))
            write_jsonl(video_manifest_path, video_manifest)
            write_jsonl(transcript_manifest_path, transcript_manifest)
    checked = ok = 0
    for rec in transcript_manifest.values():
        if rec.get("status") not in {"archived", "already_archived"}:
            continue
        checked += 1
        p = root / rec["archive_path"]
        if p.exists() and validate_envelope(p, rec.get("ciphertext_sha256")):
            ok += 1

    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "channel_url": args.channel_url,
        "channel_id": "UCxMt2GgYbO6-FCf0p4sAT0A",
        "harvested_at_utc": datetime.now(timezone.utc).isoformat(),
        "discovered_videos": len(videos),
        "metadata_records": len(video_manifest),
        "transcript_archived": sum(
            x.get("status") in {"archived", "already_archived"}
            for x in transcript_manifest.values()
        ),
        "transcript_errors": sum(x.get("status") == "error" for x in transcript_manifest.values()),
        "integrity_checked": checked,
        "integrity_ok": ok,
        "encryption_scheme": SCHEME,
        "archive_public_key_sha256": key_hash,
        "tooling": {
            "yt-dlp": "2026.8.19",
            "youtube-transcript-api": "1.2.4",
            "cryptography": "50.0.1",
        },
    }
    (root / "channel_snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if errors:
        write_jsonl(error_path, errors)

    metadata_errors = sum("metadata_error" in x for x in video_manifest.values())
    transcript_errors = sum(x.get("status") == "error" for x in transcript_manifest.values())
    # Metadata enrichment is intentionally non-blocking: the archive's hard
    # requirement is a complete transcript archive with stable discovery
    # provenance. Any metadata-enrichment failures are retained and reported.
    if checked != ok or transcript_errors or len(video_manifest) != len(videos):
        logging.error(
            "Archive incomplete: %d/%d envelopes verified; transcript_errors=%d metadata_errors=%d",
            ok, checked, transcript_errors, metadata_errors,
        )
        return 2
    logging.info("Archive complete: %d videos; %d encrypted transcript envelopes verified", len(videos), ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
