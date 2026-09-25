#!/usr/bin/env python3
"""Decrypt one Equity Income hybrid transcript envelope locally."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from scripts.archive_equity_income_keyless import hybrid_decrypt, sha256_bytes


def load_private_key(path: Path):
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise TypeError("Archive private key is not RSA")
    if key.key_size < 3072:
        raise ValueError("Archive RSA private key must be at least 3072 bits")
    return key


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-key", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-sha256", default=None)
    args = parser.parse_args()

    private_key = load_private_key(args.private_key)
    envelope = json.loads(args.input.read_text(encoding="utf-8"))
    plaintext = hybrid_decrypt(private_key, envelope)
    if args.expected_sha256 and sha256_bytes(plaintext) != args.expected_sha256:
        raise SystemExit("PLAINTEXT_HASH_MISMATCH")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(plaintext)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
