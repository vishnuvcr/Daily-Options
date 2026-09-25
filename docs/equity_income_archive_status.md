# Equity Income Archive — Current Status

Last updated: 2026-09-25 16:10 IST

## Objective

Finish a durable, deterministic Python archive of every public upload on the Equity Income YouTube channel before weekly strategy research resumes.

## Current inventory

- Channel: https://www.youtube.com/@equityincome
- Enumerated public videos: 169
- Discovery surfaces: /videos, /shorts, /streams
- Metadata inventory: 169 discovery records
- Validated encrypted transcripts: 0 in the latest completed archive snapshot
- Latest completed failed archive snapshot: 169 transcript errors; no ciphertext envelopes accepted

## Completed engineering work

1. Channel discovery is Python/yt-dlp based and de-duplicates by video ID.
2. Transcript retrieval is source-text only; no LLM transcription is used.
3. Transcript payloads are encrypted with RSA-OAEP-SHA256 + Fernet-SHA256 hybrid encryption.
4. The matching private key is kept outside the repository.
5. Archive manifests are resumable JSONL records.
6. GitHub Actions starts the pinned bgutil PO-token provider on localhost:4416.
7. Partial encrypted successes are committed even when the complete channel pass is not yet successful.
8. A regression test now covers the timestamped Markdown fallback parser.

## Current transcript acquisition ladder

For each video, the Python runner tries, in order:

1. yt-dlp subtitle extraction with PO-token-aware web/mweb clients;
2. tv, web_embedded, and android_vr yt-dlp client paths;
3. youtube-transcript-api source-caption tracks;
4. direct InnerTube caption-track retrieval;
5. direct timedtext retrieval;
6. a single documented no-key third-party transcript endpoint as a last resort, with provenance recorded as youtube-transcript-ai.

The final fallback is not treated as equivalent to a first-party YouTube caption source; its method is stored explicitly in the encrypted transcript payload and manifest.

## Acceptance gate

The archive is not complete until:

- all 169 current videos have a transcript or an explicit durable failure record;
- every accepted transcript has a non-empty snippet list;
- every accepted ciphertext passes envelope and SHA-256 integrity checks;
- manifest counts match the discovered inventory;
- a second run is idempotent for existing video IDs;
- the research program resumes only after the archive completion gate passes.

## Next execution

Trigger the default-branch archive workflow against the fixed equity-income-channel-archive-v1 branch. Treat run output as non-evidentiary until transcript counts and integrity counts are inspected.

## Strategy research status

Weekly trading research remains PAUSED. Phase 26+ strategy branches remain pre-registered and must not be evaluated using transcript interpretations until the channel archive is complete.

## Execution trigger checkpoint — 2026-09-25

The hardened archive code and fixed-branch manual workflow are committed. A new push to the default-branch trigger file has also been committed, which invokes the unattended workflow that checks out the fixed archive branch.

Trigger commit on main: a26be8c4f9ca3c07b0bbe40732557e362edc63ed.

Acceptance remains pending until the resulting GitHub Actions archive snapshot reports validated encrypted transcript envelopes and passes the full inventory/integrity gate.