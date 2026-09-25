#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, time
from pathlib import Path
import requests

VIDEO_ID = "aRjY_O6U3nQ"
URL = "https://youtubegpt.ai/api/transcript"

def fetch_segments():
    r = requests.get(
        URL,
        params={"v": VIDEO_ID, "format": "json", "lang": "en"},
        headers={"User-Agent": "Daily-Options-Phase27.7/1.0"},
        timeout=(5, 20),
    )
    r.raise_for_status()
    d = r.json()
    if not d.get("ok"):
        raise RuntimeError(str(d.get("message") or d.get("code") or "API_NOT_OK"))
    segs = [s for s in d.get("segments", []) if isinstance(s, dict) and str(s.get("text") or "").strip()]
    if not segs:
        raise RuntimeError("EMPTY_TRANSCRIPT")
    return segs

def norm(x):
    return re.sub(r"\s+", " ", str(x or "")).strip()

def contexts(segs, patterns, radius=4, limit=12):
    out = []
    rx = [re.compile(p, re.I) for p in patterns]
    for i, s in enumerate(segs):
        text = norm(s.get("text"))
        if not any(p.search(text) for p in rx):
            continue
        lo, hi = max(0, i-radius), min(len(segs), i+radius+1)
        out.append({
            "anchor_start_ms": int(float(s.get("start") or 0)),
            "anchor_text": text,
            "context": [
                {
                    "start_ms": int(float(segs[j].get("start") or 0)),
                    "text": norm(segs[j].get("text"))
                }
                for j in range(lo, hi)
            ]
        })
        if len(out) >= limit:
            break
    return out

def main():
    segs = fetch_segments()
    result = {
        "video_id": VIDEO_ID,
        "segment_count": len(segs),
        "transcript_text_sha256": hashlib.sha256(
            " ".join(norm(s.get("text")) for s in segs).encode()
        ).hexdigest(),
        "contexts": {
            "delta_02": contexts(segs, [r"0\.2\s*(?:delta|Δ)"]),
            "exit_325": contexts(segs, [r"3:25"]),
            "exit_5min_before": contexts(segs, [r"5\s*minutes?\s*(?:before|to)\s*(?:the\s+)?expir"]),
            "adjust_near": contexts(segs, [r"price is near", r"approach(?:es|ing)?\s+(?:the\s+)?short"]),
            "structure": contexts(segs, [r"short strangle", r"iron condor", r"condor", r"ratio spread", r"jade lizard"]),
            "entry": contexts(segs, [r"when (?:you|we) enter", r"entry", r"start the trade", r"take the trade"]),
            "stop": contexts(segs, [r"stop[- ]loss", r"hard stop", r"soft stop", r"\bSL\b"]),
            "range_formula": contexts(segs, [r"1[- ]sigma", r"2[- ]sigma", r"expected range", r"India VIX"]),
        },
        "source_url": "https://www.youtube.com/watch?v=" + VIDEO_ID,
        "backtest_allowed": False,
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("reports/phase27_7_air_defense_contexts.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: len(v) for k, v in result["contexts"].items()}, sort_keys=True))

if __name__ == "__main__":
    main()
