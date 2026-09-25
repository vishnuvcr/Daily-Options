from scripts.archive_equity_income import normalize_snippets, parse_vtt, parse_innertube_json3, parse_timestamped_markdown, sha256_bytes
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


def test_parse_vtt_html_unescape():
    vtt = """WEBVTT

00:00.000 --> 00:01.000
Less &amp; more &lt;than&gt;
"""
    out = parse_vtt(vtt)
    assert out[0]["text"] == "Less & more <than>"


def test_parse_innertube_json3():
    data = {
        "events": [
            {"tStartMs": 1250, "dDurationMs": 500, "segs": [{"utf8": "Hello "}, {"utf8": "world"}]},
            {"tStartMs": 2000, "dDurationMs": 500, "segs": [{"utf8": "ignored"}]},
            {"tStartMs": 2500, "dDurationMs": 500},
        ]
    }
    out = parse_innertube_json3(data)
    assert out == [
        {"start": 1.25, "duration": 0.5, "text": "Hello world"},
        {"start": 2.0, "duration": 0.5, "text": "ignored"},
    ]


def test_parse_timestamped_markdown():
    text = """Language: en

[0:00] Hello world
[1:02] Second line
"""
    out = parse_timestamped_markdown(text)
    assert out == [
        {"start": 0.0, "duration": 0.0, "text": "Hello world"},
        {"start": 62.0, "duration": 0.0, "text": "Second line"},
    ]



def test_parse_youtubegpt_segment_shape():
    data = {
        "ok": True,
        "track": {"language": "en", "name": "English", "generated": True},
        "segments": [
            {"start": 1250, "dur": 500, "text": "Hello &amp; world"},
            {"start": 2000, "dur": None, "text": "Second"},
        ],
    }
    snippets = normalize_snippets([
        {"start": data["segments"][0]["start"] / 1000, "duration": data["segments"][0]["dur"] / 1000, "text": data["segments"][0]["text"]},
        {"start": data["segments"][1]["start"] / 1000, "duration": 0.0, "text": data["segments"][1]["text"]},
    ])
    assert snippets[0]["start"] == 1.25
    assert snippets[0]["text"] == "Hello & world"
    assert snippets[1]["start"] == 2.0
