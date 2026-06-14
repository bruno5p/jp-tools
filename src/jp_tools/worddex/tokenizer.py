import re
from collections.abc import Iterable

import lxml.html

_tagger = None
_VERB_POS = frozenset({"動詞", "助動詞"})


def _get_tagger():
    global _tagger
    if _tagger is None:
        try:
            import fugashi
        except ImportError:
            raise ImportError(
                "fugashi is required: pip install fugashi unidic-lite"
            )
        _tagger = fugashi.Tagger()
    return _tagger


def _clean_sentence(text: str) -> str:
    """Strip HTML (removing <rt>/<rp> reading annotations) and furigana-plain brackets.

    Handles two formats:
    - HTML with <ruby>/<rt> tags (readings embedded in markup)
    - Furigana-plain: 漢字[かんじ] notation (used by this project's card creator)
    """
    if not text:
        return ""
    if "<" in text:
        try:
            root = lxml.html.fromstring(text)
            for elem in root.findall(".//rt") + root.findall(".//rp"):
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)
            text = root.text_content()
        except Exception:
            text = re.sub(r"<[^>]+>", "", text)
    # Strip furigana-plain: 漢字[かんじ] → 漢字
    text = re.sub(r"\[[^\]]*\]", "", text)
    return text.strip()


def _is_japanese(text: str) -> bool:
    return any(
        "぀" <= c <= "ヿ"  # hiragana + katakana
        or "一" <= c <= "鿿"  # CJK unified ideographs
        or "㐀" <= c <= "䶿"  # CJK extension A
        for c in text
    )


def _tokenize(sentence: str) -> set[str]:
    tagger = _get_tagger()
    words: set[str] = set()
    for token in tagger(sentence):
        surface = token.surface
        if not surface or not _is_japanese(surface):
            continue
        words.add(surface)
        feature = token.feature
        pos1 = getattr(feature, "pos1", None)
        if pos1 in _VERB_POS:
            orth_base = getattr(feature, "orthBase", None)
            if orth_base and orth_base != "*" and _is_japanese(orth_base):
                words.add(orth_base)
    return words


def extract_sentence_words(sentences: Iterable[str]) -> set[str]:
    """Tokenize sentences and return all surface forms plus verb dictionary forms.

    For each token MeCab identifies as a verb (動詞) or auxiliary verb (助動詞),
    the dictionary form (orthBase from UniDic) is added alongside the surface form.
    E.g. 経って → {経って, 経つ}; し (from しない) → {し, する}.
    """
    result: set[str] = set()
    for sentence in sentences:
        clean = _clean_sentence(str(sentence))
        if clean:
            result |= _tokenize(clean)
    return result
