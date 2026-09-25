# Equity Income channel archive plan

## Objective

Create a reproducible, continuously updated archive of every public Equity Income upload before restarting trading research.

The channel page identifies Equity Income and describes its focus as options selling/buying, risk-managed NIFTY/BankNIFTY setups and weekly-income tactics. citeturn454912youtube12

## Public-repository constraint

The repository is public. Full copyrighted transcripts are therefore not committed as plaintext. Instead, the branch stores encrypted transcript payloads, metadata, provenance and integrity hashes. The encryption key stays outside the repository.

This provides a durable archive without publishing the full source text.

## Acquisition method

The Python archive program:

1. Crawls /videos, /shorts and /streams.
2. De-duplicates by YouTube video ID.
3. Enriches each upload with deterministic yt-dlp metadata.
4. Retrieves transcripts with youtube-transcript-api.
5. Prefers manually authored English/Hindi tracks, then generated tracks.
6. Falls back to subtitle tracks exposed by yt-dlp.
7. Preserves timestamps and transcript provenance.
8. SHA-256 hashes the exact plaintext transcript payload.
9. Encrypts the payload with a random Fernet data key and wraps that key with the committed RSA-OAEP public key (hybrid encryption).
10. Validates the stored ciphertext envelope and SHA-256 ciphertext hash after the run.
11. Maintains resumable JSONL manifests.

The current transcript API documents direct transcript fetching and transcript-list inspection, while yt-dlp supports flat playlist extraction for channel discovery. citeturn256822search1turn256822search0

## Frozen tooling

- Python 3.12
- yt-dlp 2026.8.19
- youtube-transcript-api 1.2.4
- cryptography 50.0.1

The versions were frozen for reproducibility against current package releases. citeturn291056search1turn256822search1turn791995search0

## Keyless encryption design

No GitHub repository secret is required.

- The repository contains only the RSA public key at `config/equity_income_archive_public_key.pem`.
- Each transcript gets a fresh Fernet data key.
- The transcript is encrypted with that data key.
- The data key is wrapped with RSA-OAEP-SHA256 using the committed public key.
- GitHub Actions can encrypt but cannot decrypt.
- The matching RSA private key is stored outside GitHub and is used only by the local decrypt utility.
- The private key must never be committed to the repository.
- The local utility is `scripts/decrypt_equity_income_transcript.py`.

The ciphertext is authenticated by Fernet, and the archive records SHA-256 hashes for both plaintext provenance and ciphertext integrity.

## Completion criteria

The archive phase is complete only when:

- all public upload surfaces have been enumerated;
- every public video has a metadata record;
- every video has a validated transcript or an explicit failure/status record;
- plaintext and ciphertext hashes are recorded;
- the archive passes a full integrity check;
- a second run produces the same existing video IDs and only adds genuinely new uploads;
- no trading backtest is started before the inventory is frozen.

## Fixed-branch rule

equity-income-channel-archive-v2-hybrid-keyless is the keyless acquisition/data branch. The earlier v1 Fernet-secret design is retained as audit history. Strategy testing stays paused while this branch is being completed.


## Key management checkpoint — 2026-09-25

The keyless implementation removes the GitHub secret blocker. The public key is repository-visible; the private key is intentionally kept outside the repository. Permanent archive activation still requires preserving that private key securely.

GitHub Actions scheduled workflows only run from the repository default branch, so the automatic weekly schedule must be mirrored on `main` while the transcript data continues to live on the dedicated archive branch. citeturn445342search0turn445342search1


## Acquisition hardening checkpoint — 2026-09-25

The archive passed channel discovery (169 unique videos) but the first completed transcript pass returned 169/169 failures from YouTube anti-bot enforcement. The fixed branch now uses a bounded Python-only acquisition ladder:

1. yt-dlp subtitle extraction with the running bgutil PO-token provider for web/mweb clients;
2. additional tv/web_embedded/android_vr yt-dlp clients;
3. youtube-transcript-api source-caption tracks;
4. InnerTube caption-track retrieval;
5. direct timedtext;
6. one no-key third-party transcript endpoint as a last resort, with explicit provenance.

The no-key endpoint is queried at most once per video in the fallback path to avoid unnecessary repeated external traffic.

Partial successful encrypted transcripts are committed even when the full-channel pass remains incomplete. No weekly strategy testing is restarted until the archive completion gate is satisfied.

## Acquisition escalation checkpoint — 2026-09-25

The first proxy-first retry produced 39 validated transcripts, demonstrating that the archive pipeline and hybrid encryption are functioning. The remaining failures are now concentrated in source/service access rather than archive serialization.

Next source-preserving escalation:
1. youtubegpt.ai documented JSON caption endpoint, preserving segment timings and generated/human provenance;
2. existing Invidious clients;
3. direct yt-dlp/PO-token and YouTube caption APIs;
4. timedtext.

No LLM-generated transcript is permitted. A third-party endpoint is accepted only when the service returns source caption segments and the manifest records the acquisition method explicitly.

## Archive gate completion — 2026-09-25

The fixed channel archive now satisfies the source-acquisition gate on run 36128134111: all 169 discovered uploads have validated encrypted transcript envelopes.

Next phase begins only after the transcript inventory is frozen and deduplicated. The weekly strategy pipeline will use the archived source-caption payloads to reconstruct each distinct strategy, normalize current NSE expiry rules/costs, preregister formalizations, and then run cost-aware Base/Stress and WFA/OOS validation on separate Phase 26–35 branches.