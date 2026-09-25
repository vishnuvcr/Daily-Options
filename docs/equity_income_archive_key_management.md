# Equity Income archive key management

## Purpose

The archive uses hybrid encryption so GitHub Actions can create permanent encrypted transcript records without storing a decryption secret in GitHub.

## Repository key

Public key file:

`config/equity_income_archive_public_key.pem`

SHA-256 fingerprint:

`284f6831bd0e6bebb3afffba37ccf110a45d6a52d09647e18c888b84bdf45899`

Only this public key belongs in the repository.

## Private key

The matching RSA private key is generated outside GitHub. It is not committed, not stored as a GitHub secret, and is required only for local transcript decryption.

Keep at least two secure backups. Loss of the private key means the encrypted transcript archive cannot be decrypted.

Use:

`python scripts/decrypt_equity_income_transcript.py --private-key <private-key.pem> --input <encrypted-envelope.json> --output <transcript.json>`

The optional `--expected-sha256` argument can be used with the SHA-256 value from `data/equity_income/transcript_manifest.jsonl`.

## No-secret guarantee

The keyless workflow contains no `secrets.EQUITY_INCOME_ARCHIVE_KEY` dependency.
