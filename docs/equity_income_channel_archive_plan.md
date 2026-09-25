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
9. Encrypts the payload with Fernet in the public repository workflow.
10. Validates the stored ciphertext and recovered plaintext hash after the run.
11. Maintains resumable JSONL manifests.

The current transcript API documents direct transcript fetching and transcript-list inspection, while yt-dlp supports flat playlist extraction for channel discovery. citeturn256822search1turn256822search0

## Frozen tooling

- Python 3.12
- yt-dlp 2026.8.19
- youtube-transcript-api 1.2.4
- cryptography 50.0.1

The versions were frozen for reproducibility against current package releases. citeturn291056search1turn256822search1turn791995search0

## Secret setup

Generate a key once:

python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Store it as the GitHub repository secret EQUITY_INCOME_ARCHIVE_KEY.

Never commit the key.

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

equity-income-channel-archive-v1 is a dedicated acquisition/data branch. Strategy testing stays paused while this branch is being completed.
