"""Yomitan-style word-audio fetching.

Mirrors how Yomitan (``ext/js/media/audio-downloader.js``) resolves pronunciation
audio for a term: try a prioritized chain of sources and embed the first valid
clip. Stdlib only — this lives in the card-building layer and adds no deps.

The default chain matches the user's ``yomitan-settings.json`` order:
local audio server (``custom-json``) → jpod101 → jisho. The local server is
optional; if it isn't running the chain silently falls through. Every network
failure is swallowed (fail-soft): :meth:`AudioDownloader.fetch` returns ``None``
rather than raising, so a flaky connection never breaks a deck build.
"""

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass

# Yomitan rejects jpod101's "no audio available" placeholder mp3 by this digest.
JPOD101_NO_AUDIO_SHA256 = (
    "ae6398b5a27bc8c0a771df6c907ade794be15518174773c58c7c7ddd17098906"
)

_USER_AGENT = "Mozilla/5.0 (jp-tools audio downloader)"


@dataclass
class AudioSource:
    """One entry in the lookup chain. ``url`` is only used by ``custom-json``."""

    type: str  # "custom-json" | "jpod101" | "jisho"
    url: str = ""


DEFAULT_LOCAL_AUDIO_URL = (
    "http://localhost:8770/?expression={expression}&reading={reading}"
)

DEFAULT_SOURCES = (
    AudioSource("custom-json", DEFAULT_LOCAL_AUDIO_URL),
    AudioSource("jpod101"),
    AudioSource("jisho"),
)


class AudioDownloader:
    """Resolve and download word audio, trying each source in order."""

    def __init__(self, sources=DEFAULT_SOURCES, media_dir=".", timeout: float = 10):
        self.sources = list(sources)
        self.media_dir = media_dir
        self.timeout = timeout

    def fetch(self, expression: str, reading: str) -> str | None:
        """Return the path to a saved mp3 for ``expression``/``reading``, or None.

        Tries each configured source; the first that yields a valid clip wins.
        Never raises — any per-source error is treated as "no audio here".
        """
        for source in self.sources:
            try:
                for url in self._candidate_urls(source, expression, reading):
                    data = self._download(url)
                    if data and self._valid(source.type, data):
                        return self._save(data, expression, reading)
            except Exception:
                # Fail-soft: a broken source must not abort the chain or build.
                continue
        return None

    # -- source resolution --------------------------------------------------

    def _candidate_urls(self, source: AudioSource, expression, reading) -> list[str]:
        if source.type == "jpod101":
            query = urllib.parse.urlencode({"kanji": expression, "kana": reading})
            return [
                "https://assets.languagepod101.com/dictionary/japanese/"
                f"audiomp3.php?{query}"
            ]
        if source.type == "custom-json":
            list_url = self._subst(source.url, expression, reading)
            body = self._download(list_url)
            if not body:
                return []
            payload = json.loads(body.decode("utf-8"))
            return [s["url"] for s in payload.get("audioSources", []) if s.get("url")]
        if source.type == "jisho":
            return self._jisho_urls(expression, reading)
        return []

    def _jisho_urls(self, expression, reading) -> list[str]:
        page = self._download(f"https://jisho.org/search/{urllib.parse.quote(expression)}")
        if not page:
            return []
        html = page.decode("utf-8", "replace")
        # <audio id="audio_食べる:たべる"><source src="//..."></audio>
        marker = f'id="audio_{expression}:{reading}"'
        idx = html.find(marker)
        if idx == -1:
            return []
        m = re.search(r'<source[^>]*\ssrc="([^"]+)"', html[idx:])
        if not m:
            return []
        src = m.group(1)
        if src.startswith("//"):
            src = "https:" + src
        return [src]

    # -- download / validate / save ----------------------------------------

    def _download(self, url: str) -> bytes | None:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read()

    def _valid(self, source_type: str, data: bytes) -> bool:
        if not data:
            return False
        if source_type == "jpod101":
            digest = hashlib.sha256(data).hexdigest()
            return digest != JPOD101_NO_AUDIO_SHA256
        return True

    def _save(self, data: bytes, expression, reading) -> str:
        key = hashlib.sha1(f"{expression} {reading}".encode()).hexdigest()[:12]
        path = os.path.join(self.media_dir, f"jp_audio_{key}.mp3")
        with open(path, "wb") as f:
            f.write(data)
        return os.path.abspath(path)

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _subst(url: str, expression: str, reading: str) -> str:
        """Substitute Yomitan URL tokens; leave unknown tokens unchanged."""
        values = {
            "expression": expression,
            "term": expression,
            "reading": reading,
            "language": "ja",
        }

        def replace(match: re.Match) -> str:
            name = match.group(1)
            return urllib.parse.quote(values[name]) if name in values else match.group(0)

        return re.sub(r"\{([^}]*)\}", replace, url)
