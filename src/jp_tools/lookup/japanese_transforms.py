"""Japanese deinflection rules ported from yomitan.

The rule data in ``japanese_transforms.json`` is extracted verbatim from
yomitan's ``ext/js/language/ja/japanese-transforms.js`` (54 transforms, 834
suffix/whole-word rules). This module turns that data into a ready-to-use
:class:`LanguageTransformer` instance, :data:`JAPANESE_TRANSFORMER`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .transforms import LanguageTransformer, RawRule

_DATA_PATH = Path(__file__).parent / "japanese_transforms.json"


def _suffix_rule(suffix_in: str, suffix_out: str, c_in: list[str], c_out: list[str]) -> RawRule:
    pattern = re.compile(re.escape(suffix_in) + "$")
    cut = len(suffix_in)

    def deinflect(text: str) -> str:
        return text[: len(text) - cut] + suffix_out

    return (pattern, deinflect, c_in, c_out)


def _whole_word_rule(word: str, deinflected: str, c_in: list[str], c_out: list[str]) -> RawRule:
    pattern = re.compile("^" + re.escape(word) + "$")

    def deinflect(_text: str) -> str:
        return deinflected

    return (pattern, deinflect, c_in, c_out)


def _build() -> LanguageTransformer:
    data = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    transforms: dict[str, dict] = {}
    for tid, transform in data["transforms"].items():
        rules: list[RawRule] = []
        for rule in transform["rules"]:
            c_in = rule["conditionsIn"]
            c_out = rule["conditionsOut"]
            if rule["type"] == "suffix":
                rules.append(_suffix_rule(rule["suffixIn"], rule["suffixOut"], c_in, c_out))
            elif rule["type"] == "wholeWord":
                rules.append(_whole_word_rule(rule["word"], rule["deinflected"], c_in, c_out))
            else:  # pragma: no cover - Japanese uses only suffix/wholeWord
                raise ValueError(f"Unsupported rule type: {rule['type']}")
        transforms[tid] = {"name": transform["name"], "rules": rules}

    transformer = LanguageTransformer()
    transformer.add_descriptor(data["conditions"], transforms)
    return transformer


JAPANESE_TRANSFORMER = _build()
