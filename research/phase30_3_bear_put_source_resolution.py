#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

import requests

VIDEO_ID = "IpCuGEDxF1k"
TRANSCRIPT_URL = "https://youtubegpt.ai/api/transcript"

PATTERNS = {
    "structure": [r"bear put spread", r"put spread", r"buy.*put", r"sell.*put"],
    "entry": [r"entry", r"enter", r"start the trade", r"take the trade"],
    "entry_timing": [r"9:?30", r"10:?00", r"11:?00", r"1:?00", r"2:?00", r"morning", r"after.*open", r"before.*expiry"],
    "strike_selection": [r"strike", r"ATM", r"OTM", r"delta", r"premium", r"points?"],
    "premium_debit_credit": [r"premium", r"debit", r"credit", r"receive", r"pay"],
    "adjustment": [r"adjust", r"adjustment", r"roll", r"shift", r"move.*strike", r"protect"],
    "adjustment_timing": [r"after.*move", r"when.*price", r"if.*market", r"next day", r"expiry"],
    "stop_loss": [r"stop[- ]loss", r"stop loss", r"hard stop", r"SL\b", r"risk"],
    "profit_target": [r"target", r"book profit", r"profit booking", r"exit at"],
    "exit": [r"exit", r"close", r"square off", r"expiry", r"before expiry"],
    "days_to_expiry": [r"days? to expiry", r"weekly", r"Tuesday", r"Thursday", r"Wednesday", r"Monday", r"Friday"],
    "lot_ratio": [r"lot", r"lots", r"ratio", r"quantity", r"qty"],
    "no_trade": [r"do not trade", r"don't trade", r"avoid", r"skip"],
    "holding_period": [r"hold", r"duration", r"days?", r"overnight"],
    "capital_margin": [r"capital", r"margin", r"funds", r"₹", r"rs\.?\s*\d"],
}

def norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()

def fetch_segments():
    r = requests.get(
        TRANSCRIPT_URL,
        params={"v": VIDEO_ID, "format": "json", "lang": "en"},
        headers={"User-Agent": "Daily-Options-Phase30.3/1.0"},
        timeout=(5, 25),
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(str(data.get("message") or data.get("code") or "API_NOT_OK"))
    segments = [
        s for s in data.get("segments", [])
        if isinstance(s, dict) and norm(s.get("text"))
    ]
    if not segments:
        raise RuntimeError("EMPTY_TRANSCRIPT")
    return segments

def contextual_matches(segments, patterns, radius=4, limit=12):
    compiled = [re.compile(p, re.I) for p in patterns]
    out = []
    for i, seg in enumerate(segments):
        text = norm(seg.get("text"))
        if not any(rx.search(text) for rx in compiled):
            continue
        lo, hi = max(0, i - radius), min(len(segments), i + radius + 1)
        out.append({
            "anchor_start_ms": int(float(seg.get("start") or 0)),
            "anchor_text": text,
            "context": [
                {
                    "start_ms": int(float(segments[j].get("start") or 0)),
                    "text": norm(segments[j].get("text")),
                }
                for j in range(lo, hi)
            ],
        })
        if len(out) >= limit:
            break
    return out

def build_report(segments):
    normalized = [norm(s.get("text")) for s in segments]
    contexts = {
        field: contextual_matches(segments, pats)
        for field, pats in PATTERNS.items()
    }
    return {
        "video_id": VIDEO_ID,
        "source_url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
        "segment_count": len(segments),
        "transcript_text_sha256": hashlib.sha256(
            " ".join(normalized).encode("utf-8")
        ).hexdigest(),
        "contexts": contexts,
        "required_rule_fields": sorted(PATTERNS),
        "backtest_allowed": False,
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

def main():
    segments = fetch_segments()
    report = build_report(segments)
    Path("reports").mkdir(parents=True, exist_ok=True)
    out = Path("reports/phase30_3_bear_put_source_contexts.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "video_id": VIDEO_ID,
        "segment_count": report["segment_count"],
        "sha256": report["transcript_text_sha256"],
        "context_counts": {k: len(v) for k, v in report["contexts"].items()},
        "backtest_allowed": False,
    }, sort_keys=True))

if __name__ == "__main__":
    main()
