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
    pitch_category: str | None  # "heiban" | "atamadaka" | "nakadaka" | "odaka" | None
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


def _count_morae(reading: str) -> int:
    digraph_second = set("ぁぃぅぇぉゃゅょァィゥェォャュョ")
    count, i = 0, 0
    while i < len(reading):
        i += 2 if i + 1 < len(reading) and reading[i + 1] in digraph_second else 1
        count += 1
    return count


def _get_pitch_category(position: int | None, reading: str) -> str | None:
    if position is None:
        return None
    n = _count_morae(reading)
    if position == 0:
        return "heiban"
    if position == 1:
        return "atamadaka"
    if n > 0 and position == n:
        return "odaka"
    return "nakadaka"


class DictionarySet:
    def __init__(
        self,
        def_zips: list[str],
        pitch_zip: str | None = None,
        freq_zip: str | None = None,
    ):
        self._term_banks: list[dict] = []
        for path in def_zips:
            print(f"Loading dictionary: {path}", file=sys.stderr)
            with zipfile.ZipFile(path) as zf:
                self._term_banks.append(_load_term_banks(zf))

        self._pitch_meta: dict[str, list] = {}
        if pitch_zip:
            print(f"Loading pitch accent dictionary: {pitch_zip}", file=sys.stderr)
            try:
                with zipfile.ZipFile(pitch_zip) as zf:
                    self._pitch_meta = _load_meta_banks(zf)
            except Exception as e:
                print(f"  WARNING: could not load pitch dict: {e}", file=sys.stderr)

        self._freq_meta: dict[str, list] = {}
        if freq_zip:
            print(f"Loading frequency dictionary: {freq_zip}", file=sys.stderr)
            with zipfile.ZipFile(freq_zip) as zf:
                self._freq_meta = _load_meta_banks(zf)

        total = sum(len(b) for b in self._term_banks)
        print(f"Dictionaries loaded: {total:,} terms across {len(self._term_banks)} dict(s).", file=sys.stderr)

    def lookup(self, lemma: str) -> DictResult | None:
        for terms in self._term_banks:
            entries = terms.get(lemma, [])
            if not entries:
                continue
            best = max(entries, key=lambda e: e[4])
            expression = best[0]
            reading = best[1]
            def_tags = best[2] or ""
            raw_defs = best[5]
            pos = [t.strip() for t in def_tags.split() if t.strip()]
            definitions = _extract_text(raw_defs) if isinstance(raw_defs, list) else [str(raw_defs)]

            pitch_position = self._get_pitch(lemma, reading)
            pitch_category = _get_pitch_category(pitch_position, reading)
            frequency = self._get_frequency(lemma, reading)

            return DictResult(
                expression=expression,
                reading=reading,
                definitions=definitions,
                pos=pos,
                pitch_position=pitch_position,
                pitch_category=pitch_category,
                frequency=frequency,
            )
        return None

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


def get_dict(
    def_zips: list[str],
    pitch_zip: str | None = None,
    freq_zip: str | None = None,
) -> DictionarySet:
    return DictionarySet(def_zips, pitch_zip=pitch_zip, freq_zip=freq_zip)
