# Equity Income research archive

Source channel: https://www.youtube.com/@equityincome

This directory is maintained by the fixed equity-income-channel-archive-v1 branch.

Public-safe repository records:
- video_manifest.jsonl — metadata for every discovered public upload.
- transcript_manifest.jsonl — transcript provenance, language, hashes and archive paths.
- channel_snapshot.json — latest acquisition summary.
- archive_errors.jsonl — explicit transcript/metadata failures.
- transcripts_encrypted/*.json.fernet — encrypted transcript payloads.

Because the repository is public, plaintext source transcripts are not committed. The Python program can also write a private/local plaintext cache with --mode private.

Transcript acquisition is performed by Python tooling only. No language model is involved in discovery or fetching.
