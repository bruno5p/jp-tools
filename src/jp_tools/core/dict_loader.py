import json
import sys
import zipfile
from dataclasses import dataclass


@dataclass
class DictResult:
    expression: str
    reading: str
    definitions: list[str]
    pos: list[str]
    pitch_position: int | None
    frequency: int | None


def _extract_text(definitions) -> list[str]:
    """Flatten Yomitan definition entries (strings or structured-content) to plain strings."""
    out = []
    for d in definitions:
        if isinstance(d, str):
            out.append(d)
        elif isinstance(d, dict):
            content_type = d.get("type", "")
            if content_type == "structured-content":
                out.append(_flatten_structured(d.get("content", "")))
            elif content_type == "text":
                out.append(d.get("text", ""))
            elif content_type == "image":
                pass
            else:
                text = d.get("text") or d.get("value") or ""
                if text:
                    out.append(str(text))
        elif isinstance(d, list):
            out.extend(_extract_text(d))
    return [s for s in out if s.strip()]


def _flatten_structured(node) -> str:
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_flatten_structured(n) for n in node)
    if isinstance(node, dict):
        content = node.get("content")
        if content is not None:
            return _flatten_structured(content)
        text = node.get("text", "")
        return str(text) if text else ""
    return ""


def _load_term_banks(zf: zipfile.ZipFile) -> dict:
    terms: dict[str, list] = {}
    bank_files = sorted(n for n in zf.namelist() if n.startswith("term_bank_") and n.endswith(".json"))
    for fname in bank_files:
        entries = json.loads(zf.read(fname))
        for entry in entries:
            key = entry[0]
            terms.setdefault(key, []).append(entry)
    return terms


def _load_meta_banks(zf: zipfile.ZipFile) -> dict:
    meta: dict[str, list] = {}
    bank_files = sorted(n for n in zf.namelist() if n.startswith("term_meta_bank_") and n.endswith(".json"))
    for fname in bank_files:
        entries = json.loads(zf.read(fname))
        for entry in entries:
            key = entry[0]
            meta.setdefault(key, []).append(entry)
    return meta


class DictionarySet:
    def __init__(self, jmdict_zip: str, kanjium_zip: str | None = None, freq_zip: str | None = None):
        print("Loading JMdict/Jitendex dictionary...", file=sys.stderr)
        with zipfile.ZipFile(jmdict_zip) as zf:
            self._terms = _load_term_banks(zf)
            self._jmdict_meta = _load_meta_banks(zf)

        self._pitch_meta: dict[str, list] = {}
        if kanjium_zip:
            print("Loading pitch accent dictionary...", file=sys.stderr)
            with zipfile.ZipFile(kanjium_zip) as zf:
                self._pitch_meta = _load_meta_banks(zf)

        self._freq_meta: dict[str, list] = {}
        if freq_zip:
            print("Loading frequency dictionary...", file=sys.stderr)
            with zipfile.ZipFile(freq_zip) as zf:
                self._freq_meta = _load_meta_banks(zf)

        print(f"Dictionaries loaded: {len(self._terms):,} terms.", file=sys.stderr)

    def lookup(self, lemma: str) -> DictResult | None:
        entries = self._terms.get(lemma, [])
        if not entries:
            return None

        best = max(entries, key=lambda e: e[4])  # sort by score (index 4)
        expression = best[0]
        reading = best[1]
        def_tags = best[2] or ""
        raw_defs = best[5]
        pos = [t.strip() for t in def_tags.split() if t.strip()]
        definitions = _extract_text(raw_defs) if isinstance(raw_defs, list) else [str(raw_defs)]

        pitch_position = self._get_pitch(lemma, reading)
        frequency = self._get_frequency(lemma, reading)

        return DictResult(
            expression=expression,
            reading=reading,
            definitions=definitions,
            pos=pos,
            pitch_position=pitch_position,
            frequency=frequency,
        )

    def _get_pitch(self, lemma: str, reading: str) -> int | None:
        for entry in self._pitch_meta.get(lemma, []):
            if entry[1] != "pitch":
                continue
            data = entry[2]
            if not isinstance(data, dict):
                continue
            pitches = data.get("pitches", [])
            if pitches and data.get("reading", reading) == reading:
                return pitches[0].get("position")
        for entry in self._pitch_meta.get(lemma, []):
            if entry[1] != "pitch":
                continue
            data = entry[2]
            if isinstance(data, dict):
                pitches = data.get("pitches", [])
                if pitches:
                    return pitches[0].get("position")
        return None

    def _get_frequency(self, lemma: str, reading: str) -> int | None:
        for entry in self._freq_meta.get(lemma, []):
            if entry[1] != "freq":
                continue
            data = entry[2]
            if not isinstance(data, dict):
                if isinstance(data, (int, float)):
                    return int(data)
                continue
            freq_data = data.get("frequency")
            if isinstance(freq_data, dict):
                return freq_data.get("value")
            if isinstance(freq_data, (int, float)):
                return int(freq_data)
        return None


_cache: DictionarySet | None = None


def get_dict(jmdict_zip: str, kanjium_zip: str | None = None, freq_zip: str | None = None) -> DictionarySet:
    global _cache
    if _cache is None:
        _cache = DictionarySet(jmdict_zip, kanjium_zip, freq_zip)
    return _cache
