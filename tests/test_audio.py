"""Unit tests for the Yomitan-style word-audio downloader (no network)."""

import json

from jp_tools.anki.audio import (
    JPOD101_NO_AUDIO_SHA256,
    AudioDownloader,
    AudioSource,
)


def test_subst_tokens():
    sub = AudioDownloader._subst
    url = "http://localhost:8770/?expression={expression}&reading={reading}&lang={language}"
    assert sub(url, "食べる", "たべる") == (
        "http://localhost:8770/?expression=%E9%A3%9F%E3%81%B9%E3%82%8B"
        "&reading=%E3%81%9F%E3%81%B9%E3%82%8B&lang=ja"
    )
    # {term} is an alias for the expression; unknown tokens are left untouched.
    assert sub("x={term}&y={unknown}", "犬", "いぬ") == "x=%E7%8A%AC&y={unknown}"


def test_valid_basic_rules():
    dl = AudioDownloader()
    # Empty bytes are never valid.
    assert dl._valid("jpod101", b"") is False
    assert dl._valid("custom-json", b"") is False
    # Ordinary bytes pass (jpod101 only rejects the one known placeholder digest).
    assert dl._valid("jpod101", b"real mp3 data") is True
    assert dl._valid("jisho", b"data") is True


def test_jpod101_exact_placeholder_digest_rejected(monkeypatch):
    """The byte string Yomitan rejects must fail validation for jpod101."""
    dl = AudioDownloader()

    # Patch hashlib so the validator sees the known-bad digest for our sentinel.
    class _Fake:
        def hexdigest(self):
            return JPOD101_NO_AUDIO_SHA256

    monkeypatch.setattr("jp_tools.anki.audio.hashlib.sha256", lambda data: _Fake())
    assert dl._valid("jpod101", b"anything") is False


def test_custom_json_parsing(monkeypatch, tmp_path):
    dl = AudioDownloader(
        sources=[AudioSource("custom-json", "http://localhost:8770/?expression={expression}")],
        media_dir=str(tmp_path),
    )
    list_payload = json.dumps(
        {
            "type": "audioSourceList",
            "audioSources": [
                {"name": "NHK", "url": "http://localhost:8770/audio/nhk.mp3"},
                {"name": "Forvo", "url": "http://localhost:8770/audio/forvo.mp3"},
            ],
        }
    ).encode("utf-8")

    audio_bytes = b"ID3 fake mp3 bytes"

    def fake_download(url):
        if url.startswith("http://localhost:8770/?expression="):
            return list_payload
        if url == "http://localhost:8770/audio/nhk.mp3":
            return audio_bytes
        return None

    monkeypatch.setattr(dl, "_download", fake_download)

    path = dl.fetch("食べる", "たべる")
    assert path is not None
    assert path.endswith(".mp3")
    with open(path, "rb") as f:
        assert f.read() == audio_bytes


def test_fetch_returns_none_when_all_sources_fail(monkeypatch, tmp_path):
    dl = AudioDownloader(media_dir=str(tmp_path))

    def boom(url):
        raise OSError("network down")

    monkeypatch.setattr(dl, "_download", boom)
    # Fail-soft: never raises, just yields no audio.
    assert dl.fetch("食べる", "たべる") is None
