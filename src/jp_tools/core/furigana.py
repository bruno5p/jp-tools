"""Furigana rendering for Anki cards.

This is the only module that needs fugashi/MeCab: it tokenizes a sentence to
attach per-token readings. Word-level dictionary lookup and reading resolution
now live in :mod:`jp_tools.core.lookup` (yomitan-style deinflection).
"""

import sys

try:
    import fugashi
    import jaconv
except ImportError as e:
    sys.exit(f"Missing dependency: {e}\n  pip install fugashi unidic-lite jaconv")


_tagger: fugashi.Tagger | None = None


def _get_tagger() -> fugashi.Tagger:
    global _tagger
    if _tagger is None:
        _tagger = fugashi.Tagger()
    return _tagger


def _kata_to_hira(text: str) -> str:
    return jaconv.kata2hira(text)


def _has_kanji(text: str) -> bool:
    return any('一' <= c <= '鿿' or '㐀' <= c <= '䶿' for c in text)


def get_furigana_plain(word: str, reading: str) -> str:
    """Return Yomitan furigana-plain format: 日本語[にほんご] for kanji words, plain reading otherwise."""
    if not word or not reading:
        return word or reading or ""
    if not _has_kanji(word):
        return reading
    return f"{word}[{reading}]"


def _get_token_reading(token) -> str | None:
    feature = token.feature
    try:
        r = getattr(feature, 'kana', None) or getattr(feature, 'reading', None)
    except Exception:
        return None
    if r and r != "*":
        return _kata_to_hira(r)
    return None


def get_sentence_furigana(sentence: str) -> str:
    """Return sentence with per-token furigana: 電気[でんき] は 大事[たいじ] だ。"""
    if not sentence:
        return ""
    tagger = _get_tagger()
    parts = []
    for token in tagger(sentence):
        surface = token.surface
        reading = _get_token_reading(token)
        if reading and reading != surface and _has_kanji(surface):
            parts.append(f"{surface}[{reading}]")
        else:
            parts.append(surface)
    return " ".join(parts)
