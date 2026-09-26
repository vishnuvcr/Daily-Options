# Phase 30.13 — Equity Income Low-VIX Diagonal source resolution

## Candidate
**Retail Option Seller's Diagonal Setup for Low Vix** — YouTube video ID `6_W4UpFsehs`, published 2025-12-26.

## Purpose
Resolve source-faithful mechanics before any option P&L is calculated. This phase is evidence acquisition/classification only.

## Research questions
1. What exact diagonal legs are opened?
2. Which expiry is used for each leg and how is expiry selected?
3. What is the exact short/long strike construction?
4. What low-VIX threshold/condition is source-explicit?
5. What is the entry day and clock?
6. What premium/debit/credit rule is used?
7. What adjustment trigger and leg movement are specified?
8. What stop-loss, target/profit-lock and time exit are specified?
9. What position ratio and capital convention are stated?
10. Which rules are source-explicit versus examples/inferences?

## Evidence method
- Acquire captions with Python tooling only; do not use model-generated transcript text as primary evidence.
- Prefer official YouTube caption tracks through `yt-dlp`; preserve raw VTT/metadata and SHA-256 hashes.
- Normalize caption text deterministically and extract timestamped contextual windows around terms such as diagonal, calendar, expiry, strike, premium, VIX, adjustment, stop, target, exit, lot, and time.
- Classify each required field as SOURCE-EXPLICIT, CONFLICTING, SOURCE-INFERRED, or UNSPECIFIED.
- Public video description is secondary corroboration only.

## P&L gate
Backtest is forbidden until all economically material fields are resolved and an exact-expiry/lot join is proven. If any essential field remains unresolved, close as SOURCE-BLOCKED rather than inventing it.

## Downstream sequence
- 30.13 source resolution
- 30.14 contract/lot readiness if source-resolved
- 30.15 bounded numerical matrix
- 30.16 nested WFA + later-period OOS if numerical gate passes

## Weekly promotion gate
Mean weekly net >= ₹5,000; median >= ₹5,000; profitable-week rate >=70%; >=20 completed weeks; >=80% execution coverage; Base and doubled-slippage Stress; no test-period tuning.

## Status
OPEN — source resolution only.


## Closure — 2026-09-26

Phase 30.13 is **SOURCE-BLOCKED / DATA-LIMITED**. The public YouTube page is discoverable, but deterministic Python caption acquisition failed from GitHub Actions: yt-dlp returned YouTube bot verification across web_safari/android/web_embedded/web clients, and YouTubeTranscriptApi returned an IP-blocked/cloud-provider response. No transcript text was accepted as primary evidence.

Therefore no payoff, strike, expiry, entry, adjustment, stop, target or exit rule was invented and **no P&L was calculated**. The candidate remains eligible for future reopening only if a reproducible non-bot primary-evidence acquisition path becomes available.
