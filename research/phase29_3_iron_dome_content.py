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
import subprocess
import tempfile
from datetime import date, timedelta
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download
import requests
from urllib.parse import quote
from yt_dlp import YoutubeDL
from yt_dlp.extractor.youtube._base import INNERTUBE_CLIENTS

PREFERRED_LANGS = ("en", "en-IN", "hi")
INVIDIOUS_INSTANCES = (
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://yt.chocolatemoo53.com",
    "https://invidious.tiekoetter.com",
)

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


def transcript_with_ytdlp(video_id: str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "%(id)s.%(ext)s"
        cmd = [
            "yt-dlp", "--quiet", "--no-warnings", "--skip-download",
            "--write-auto-subs", "--sub-langs", "en.*,en",
            "--sub-format", "vtt", "--output", str(out),
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "yt-dlp failed").strip())
        files = sorted(Path(td).glob(f"{video_id}*.vtt"))
        if not files:
            raise RuntimeError("yt-dlp completed but produced no VTT subtitle file")
        text_lines = []
        for line in files[0].read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line == "WEBVTT" or "-->" in line or line.isdigit():
                continue
            text_lines.append(re.sub(r"<[^>]+>", "", line))
        full = norm_text(" ".join(text_lines))
        sha = hashlib.sha256(full.encode("utf-8")).hexdigest()
        evidence = []
        lower_lines = [norm_text(x) for x in text_lines if norm_text(x)]
        for i, txt in enumerate(lower_lines):
            lower = txt.lower()
            if any(term in lower for term in RULE_TERMS) or NUMBER_PAT.search(txt):
                context = " ".join(lower_lines[max(0, i - 1): min(len(lower_lines), i + 2)])
                evidence.append({
                    "text": norm_text(context)[:320],
                    "trigger_terms": sorted({term for term in RULE_TERMS if term in lower})[:8],
                })
        return {
            "status": "OK",
            "video_id": video_id,
            "method": "yt-dlp-auto-subs-vtt",
            "sha256": sha,
            "snippet_count": len(lower_lines),
            "evidence_count": len(evidence),
            "evidence": evidence[:160],
        }



def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize_snippets(items) -> list[dict]:
    out = []
    seen = set()
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
        if key in seen:
            continue
        seen.add(key)
        out.append({"start": round(start, 3), "duration": round(duration, 3), "text": text})
    return out


def parse_vtt_timestamp(value: str) -> float:
    value = value.replace(",", ".")
    parts = value.split(":")
    if len(parts) == 2:
        return float(parts[0]) * 60.0 + float(parts[1])
    return float(parts[0]) * 3600.0 + float(parts[1]) * 60.0 + float(parts[2])


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
        except (ValueError, IndexError):
            i += 1
            continue
        i += 1
        parts = []
        while i < len(lines) and lines[i].strip():
            parts.append(re.sub(r"<[^>]+>", "", lines[i].strip()))
            i += 1
        text = clean_text(" ".join(parts))
        if text:
            out.append({"start": start, "duration": max(0.0, stop - start), "text": text})
    return normalize_snippets(out)


def fetch_external_transcript_service(video_id: str):
    endpoints = (
        "https://youtube-transcript.ai/transcript/{video_id}.txt?lang=en",
    )
    errors = []
    headers = {"User-Agent": "Daily-Options-Phase29.3/1.0"}
    for template in endpoints:
        url = template.format(video_id=quote(video_id, safe=""))
        try:
            response = requests.get(url, headers=headers, timeout=(5, 15))
            if response.status_code != 200 or not response.text.strip():
                errors.append(f"HTTP_{response.status_code}")
                continue
            snippets = parse_timestamped_markdown(response.text)
            if snippets:
                match = re.search(r"^Language:\s*([^\s·]+)", response.text, flags=re.MULTILINE)
                lang = match.group(1) if match else "en"
                return snippets, lang, lang, None, "youtube-transcript-ai"
            errors.append("NO_TIMESTAMPED_SEGMENTS")
        except requests.RequestException as exc:
            errors.append(repr(exc))
    return None, errors


def fetch_youtubegpt(video_id: str):
    url = "https://youtubegpt.ai/api/transcript"
    try:
        response = requests.get(
            url,
            params={"v": video_id, "format": "json", "lang": "en"},
            headers={"User-Agent": "Daily-Options-Phase29.3/1.0"},
            timeout=(5, 15),
        )
        if response.status_code != 200 or not response.text.strip():
            return None, f"HTTP_{response.status_code}"
        data = response.json()
        if not data.get("ok"):
            return None, str(data.get("code") or data.get("message") or "API_NOT_OK")
        track = data.get("track") or {}
        snippets = []
        for seg in data.get("segments") or []:
            if not isinstance(seg, dict):
                continue
            text = clean_text(seg.get("text", ""))
            if not text:
                continue
            try:
                start = float(seg.get("start", 0)) / 1000.0
                duration = float(seg.get("dur", 0)) / 1000.0
            except (TypeError, ValueError):
                continue
            snippets.append({"start": start, "duration": duration, "text": text})
        snippets = normalize_snippets(snippets)
        if not snippets:
            return None, "NO_SEGMENTS"
        lang = str(track.get("language") or "en")
        return snippets, lang, str(track.get("name") or lang), track.get("generated"), "youtubegpt-json"
    except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
        return None, repr(exc)


def fetch_invidious(video_id: str):
    headers = {"User-Agent": "Daily-Options-Phase29.3/1.0"}
    errors = []
    for instance in INVIDIOUS_INSTANCES:
        base = instance.rstrip("/")
        try:
            index = requests.get(
                f"{base}/api/v1/captions/{video_id}",
                headers=headers,
                timeout=(3, 10),
            )
            if index.status_code != 200:
                errors.append(f"{base}:HTTP_{index.status_code}")
                continue
            data = index.json()
            candidates = []
            for cap in data.get("captions") or []:
                lang = cap.get("languageCode", "")
                label = cap.get("label", "")
                url = cap.get("url")
                if not lang or not url:
                    continue
                generated = "auto-generated" in str(label).lower()
                rank_lang = PREFERRED_LANGS.index(lang) if lang in PREFERRED_LANGS else 99
                candidates.append((int(generated), rank_lang, lang, label, url, generated))
            candidates.sort()
            for _, _, lang, label, url, generated in candidates:
                target = url if str(url).startswith("http") else f"{base}{url}"
                response = requests.get(target, headers=headers, timeout=(3, 10))
                if response.status_code != 200 or not response.text.strip():
                    continue
                snippets = parse_vtt(response.text)
                if snippets:
                    return snippets, lang, label or lang, generated, "invidious-captions"
            errors.append(f"{base}:NO_USABLE_CAPTION")
        except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
            errors.append(f"{base}:{exc!r}")
    return None, errors


def fetch_ytdlp_subtitles(video_id: str):
    profiles = ("tv", "tv_downgraded", "web_embedded", "android_vr")
    errors = []
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    for client_name in profiles:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "socket_timeout": 15,
            "retries": 1,
            "extractor_args": {"youtube": {"player_client": [client_name]}},
        }
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                tracks = []
                for field, generated in (("subtitles", False), ("automatic_captions", True)):
                    for lang, formats in (info.get(field) or {}).items():
                        for track in formats or []:
                            url = track.get("url")
                            if not url:
                                continue
                            rank_lang = PREFERRED_LANGS.index(lang) if lang in PREFERRED_LANGS else 99
                            rank_ext = 0 if track.get("ext") == "vtt" else 1
                            tracks.append((int(generated), rank_lang, rank_ext, lang, generated, url))
                tracks.sort()
                for _, _, _, lang, generated, url in tracks:
                    raw = ydl.urlopen(url).read().decode("utf-8", errors="replace")
                    snippets = parse_vtt(raw)
                    if snippets:
                        return snippets, lang, lang, generated, f"yt-dlp-subtitles:{client_name}"
                errors.append(f"{client_name}:NO_USABLE_SUBTITLE")
        except Exception as exc:
            errors.append(f"{client_name}:{exc!r}")
    return None, errors


def fetch_youtube_transcript_api(video_id: str):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        tracks = list(api.list(video_id))
        ranked = []
        for track in tracks:
            code = getattr(track, "language_code", "")
            generated = bool(getattr(track, "is_generated", False))
            lang_rank = PREFERRED_LANGS.index(code) if code in PREFERRED_LANGS else 99
            ranked.append((int(generated), lang_rank, code, track))
        ranked.sort()
        for _, _, code, track in ranked:
            try:
                fetched = track.fetch()
                raw = fetched.to_raw_data() if hasattr(fetched, "to_raw_data") else list(fetched)
                snippets = normalize_snippets(raw)
                if snippets:
                    return snippets, code, getattr(track, "language", code), bool(getattr(track, "is_generated", False)), "youtube-transcript-api"
            except Exception:
                continue
        return None, "NO_USABLE_TRANSCRIPT_API_TRACK"
    except Exception as exc:
        return None, repr(exc)


def parse_innertube_json3(data: dict) -> list[dict]:
    out = []
    for event in data.get("events") or []:
        if not isinstance(event, dict) or not event.get("segs"):
            continue
        text = "".join(str(seg.get("utf8", "")) for seg in event.get("segs") or [] if isinstance(seg, dict))
        if text.strip():
            out.append({
                "start": float(event.get("tStartMs", 0)) / 1000.0,
                "duration": float(event.get("dDurationMs", 0)) / 1000.0,
                "text": clean_text(text),
            })
    return normalize_snippets(out)


def fetch_innertube(video_id: str):
    session = requests.Session()
    for client_name in ("tv", "tv_downgraded", "web_embedded"):
        cfg = INNERTUBE_CLIENTS.get(client_name)
        if not cfg:
            continue
        ctx = json.loads(json.dumps(cfg["INNERTUBE_CONTEXT"]))
        client = ctx.setdefault("client", {})
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://www.youtube.com",
            "User-Agent": client.get("userAgent") or "Mozilla/5.0",
            "X-YouTube-Client-Name": str(cfg.get("INNERTUBE_CONTEXT_CLIENT_NAME", "")),
            "X-YouTube-Client-Version": str(client.get("clientVersion", "")),
        }
        try:
            response = session.post(
                "https://www.youtube.com/youtubei/v1/player",
                params={"prettyPrint": "false"},
                json={"context": ctx, "videoId": video_id, "contentCheckOk": True, "racyCheckOk": True},
                headers=headers,
                timeout=(3, 8),
            )
            if response.status_code != 200:
                continue
            data = response.json()
            tracks = data.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
            ranked = []
            for track in tracks or []:
                code = track.get("languageCode", "")
                generated = track.get("kind") == "asr"
                rank_lang = PREFERRED_LANGS.index(code) if code in PREFERRED_LANGS else 99
                ranked.append((int(generated), rank_lang, code, generated, track))
            ranked.sort()
            for _, _, code, generated, track in ranked:
                base_url = track.get("baseUrl")
                if not base_url:
                    continue
                cap = session.get(
                    base_url,
                    params={"fmt": "json3"},
                    headers={"User-Agent": headers["User-Agent"]},
                    timeout=(3, 8),
                )
                if cap.status_code == 200 and cap.text.strip():
                    snippets = parse_innertube_json3(cap.json())
                    if snippets:
                        return snippets, code, code, generated, "youtube-innertube"
        except (requests.RequestException, ValueError, TypeError, KeyError):
            continue
    return None, "INNER_TUBE_CAPTION_NOT_FOUND"


def fetch_timedtext(video_id: str):
    session = requests.Session()
    for lang, generated in (("en", True), ("en", False), ("hi", True)):
        try:
            response = session.get(
                "https://www.youtube.com/api/timedtext",
                params={"v": video_id, "lang": lang, "fmt": "vtt", **({"kind": "asr"} if generated else {})},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=(3, 5),
            )
            if response.status_code == 200 and response.text.strip():
                snippets = parse_vtt(response.text)
                if snippets:
                    return snippets, lang, lang, generated, "youtube-timedtext"
        except requests.RequestException:
            continue
    return None, "TIMEDTEXT_NOT_FOUND"


def parse_timestamped_markdown(text: str) -> list[dict]:
    out = []
    stamp = re.compile(r"^\[(\d{1,3}):(\d{2})(?::(\d{2}))?\]\s*(.+?)\s*$")
    for line in text.splitlines():
        match = stamp.match(line.strip())
        if not match:
            continue
        a, b, c, caption = match.groups()
        start = int(a) * (3600 if c else 60) + int(b) * (60 if c else 1) + (int(c) if c else 0)
        caption = clean_text(caption)
        if caption:
            out.append({"start": float(start), "duration": 0.0, "text": caption})
    return normalize_snippets(out)


def fetch_transcript(video_id: str):
    errors = []

    external = fetch_external_transcript_service(video_id)
    if external[0] is not None:
        return external
    errors.append(f"youtube-transcript-ai:{external[1]}")

    youtubegpt = fetch_youtubegpt(video_id)
    if youtubegpt[0] is not None:
        return youtubegpt
    errors.append(f"youtubegpt:{youtubegpt[1]}")

    inv = fetch_invidious(video_id)
    if inv[0] is not None:
        return inv
    errors.append(f"invidious:{inv[1]}")

    ytdlp = fetch_ytdlp_subtitles(video_id)
    if ytdlp[0] is not None:
        return ytdlp
    errors.append(f"yt-dlp:{ytdlp[1]}")

    api = fetch_youtube_transcript_api(video_id)
    if api[0] is not None:
        return api
    errors.append(f"youtube-transcript-api:{api[1]}")

    inner = fetch_innertube(video_id)
    if inner[0] is not None:
        return inner
    errors.append(f"youtube-innertube:{inner[1]}")

    timed = fetch_timedtext(video_id)
    if timed[0] is not None:
        return timed
    errors.append(f"youtube-timedtext:{timed[1]}")

    raise RuntimeError("TRANSCRIPT_FETCH_FAILED: " + " | ".join(errors[-12:]))


def transcript(video_id: str) -> dict:
    snippets, language, label, generated, source = fetch_transcript(video_id)
    full = " ".join(x["text"] for x in snippets)
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
        "language": language,
        "track_label": label,
        "generated": generated,
        "source": source,
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
        except Exception as first_exc:
            try:
                transcript_rows.append(transcript_with_ytdlp(v["video_id"]))
            except Exception as second_exc:
                transcript_rows.append({
                    "status": "ERROR",
                    "video_id": v["video_id"],
                    "error": f"youtube-transcript-api: {first_exc}; yt-dlp fallback: {second_exc}",
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

    Path("reports/phase29_3_expiry_content_checks.json").write_text(
        json.dumps({"checks": content_checks}, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

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
