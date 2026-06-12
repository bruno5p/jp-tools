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


def get_dictionary_form(sentence: str, surface_hint: str) -> str:
    """Return the dictionary form (lemma) of the token in sentence that best matches surface_hint.

    Falls back to surface_hint itself if no matching token is found.
    """
    tagger = _get_tagger()
    tokens = list(tagger(sentence))

    # Try exact surface match first
    for token in tokens:
        if token.surface == surface_hint:
            lemma = _get_lemma(token)
            if lemma:
                return lemma

    # Try partial/substring match (e.g. user typed kanji, token has okurigana)
    for token in tokens:
        if surface_hint in token.surface or token.surface in surface_hint:
            lemma = _get_lemma(token)
            if lemma:
                return lemma

    return surface_hint


def _get_lemma(token) -> str | None:
    """Extract lemma from a fugashi token. Handles both UniDic and UniDic-lite feature layouts."""
    feature = token.feature
    if feature is None:
        return None
    # unidic-lite exposes feature as a named tuple; lemma is at index 10
    try:
        lemma = feature.lemma
        if lemma and lemma != "*":
            # UniDic lemma may have reading appended as "word-reading", strip it
            return lemma.split("-")[0]
    except AttributeError:
        pass
    # Fallback: raw feature string, lemma is field 10 (0-indexed)
    try:
        parts = str(feature).split(",")
        if len(parts) > 10:
            lemma = parts[10].strip()
            if lemma and lemma != "*":
                return lemma.split("-")[0]
    except Exception:
        pass
    return token.surface


def get_reading(sentence: str, surface_hint: str) -> str:
    """Return the kana reading (hiragana) for the token matching surface_hint."""
    tagger = _get_tagger()
    tokens = list(tagger(sentence))

    for token in tokens:
        if token.surface == surface_hint or surface_hint in token.surface:
            feature = token.feature
            reading = None
            try:
                reading = feature.kana or feature.reading
            except AttributeError:
                pass
            if reading and reading != "*":
                return _kata_to_hira(reading)
    return surface_hint


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
