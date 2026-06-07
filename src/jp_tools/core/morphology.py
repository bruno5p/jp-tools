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
