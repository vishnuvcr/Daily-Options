from scripts.archive_equity_income import normalize_snippets, parse_vtt, sha256_bytes
from scripts.archive_equity_income_keyless import hybrid_decrypt, hybrid_encrypt

def test_normalize_snippets_collapses_duplicate_caption():
    raw = [
        {"text": "Hello", "start": 0, "duration": 1},
        {"text": "  Hello  ", "start": 0, "duration": 1},
        {"text": "World", "start": 1.25, "duration": 0.5},
    ]
    out = normalize_snippets(raw)
    assert [x["text"] for x in out] == ["Hello", "World"]

def test_parse_vtt():
    vtt = """WEBVTT

00:00.000 --> 00:01.250
Hello world

00:01.250 --> 00:03.000
Second line
"""
    out = parse_vtt(vtt)
    assert len(out) == 2
    assert out[0]["text"] == "Hello world"
    assert out[1]["start"] == 1.25

def test_hash_is_stable():
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_hybrid_encryption_round_trip():
    from cryptography.hazmat.primitives.asymmetric import rsa
    private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    plaintext = b"immutable transcript fixture"
    envelope = hybrid_encrypt(private.public_key(), plaintext)
    assert hybrid_decrypt(private, envelope) == plaintext
    assert envelope["encryption_scheme"] == "RSA-OAEP-SHA256+FERNET-SHA256"
