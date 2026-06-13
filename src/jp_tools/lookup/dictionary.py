"""Dictionary loading and yomitan-style term lookup.

Loads yomitan term/meta banks and exposes :meth:`DictionarySet.find_term`, a
faithful port of yomitan's ``findTerms`` flow:

1. Scan the input longest-first, trimming one character off the end each pass.
2. Deinflect every substring via :data:`JAPANESE_TRANSFORMER` (chained rules).
3. Look each candidate up against both the expression and reading indexes.
4. Keep a match only if the deinflection's conditions are compatible with the
   term's ``rules`` field (part-of-speech gating).
5. Rank by source length (longest) -> inflection-chain length (shortest) ->
   dictionary priority -> score, and return the winner.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from .japanese_transforms import JAPANESE_TRANSFORMER
from .transforms import LanguageTransformer


@dataclass
class DictResult:
    expression: str
    reading: str
    definitions: list[str]
    pos: list[str]
    pitch_position: int | None
    pitch_category: str | None  # "heiban" | "atamadaka" | "nakadaka" | "odaka" | None
    # One (label, rank) pair per frequency list that contains this word, in the
    # order the lists were loaded. Lists missing the word are simply omitted.
    frequencies: list[tuple[str, int]]
    dict_name: str = ""


@dataclass
class _Entry:
    expression: str
    reading: str
    def_tags: str
    rules: str
    score: int
    glossary: list
    dict_index: int


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


def _alphabet_ratio(result: "DictResult") -> float:
    """Ratio of ASCII a-z/A-Z characters to total characters across all definitions."""
    text = "".join(result.definitions)
    if not text:
        return 0.0
    return sum(1 for c in text if c.isascii() and c.isalpha()) / len(text)


def _bank_files(directory: Path, prefix: str) -> list[Path]:
    """Yomitan bank files (``term_bank_1.json`` …) in numeric order within ``directory``."""
    return sorted(
        directory.glob(f"{prefix}*.json"),
        key=lambda p: int("".join(filter(str.isdigit, p.stem)) or 0),
    )


def _load_meta_banks(directory: Path) -> dict:
    meta: dict[str, list] = {}
    for fname in _bank_files(directory, "term_meta_bank_"):
        for entry in json.loads(fname.read_text(encoding="utf-8")):
            meta.setdefault(entry[0], []).append(entry)
    return meta


def _read_dict_title(directory: Path) -> str | None:
    """The human-readable title from a Yomitan dictionary's ``index.json``."""
    index = directory / "index.json"
    if not index.is_file():
        return None
    try:
        return json.loads(index.read_text(encoding="utf-8")).get("title")
    except (json.JSONDecodeError, OSError):
        return None


def _coerce_freq_value(data) -> int | None:
    """Pull the numeric rank out of any Yomitan ``freq`` payload shape."""
    if isinstance(data, (int, float)):
        return int(data)
    if isinstance(data, dict):
        if isinstance(data.get("value"), (int, float)):
            return int(data["value"])
        freq = data.get("frequency")
        if isinstance(freq, (int, float)):
            return int(freq)
        if isinstance(freq, dict) and isinstance(freq.get("value"), (int, float)):
            return int(freq["value"])
    return None


def _extract_freq(meta: dict, expression: str, reading: str) -> int | None:
    """Look ``expression``/``reading`` up in one frequency meta bank.

    Entries that pin a specific ``reading`` are preferred only when it matches; a
    reading-mismatched entry is kept as a last-resort fallback.
    """
    fallback: int | None = None
    for key in (expression, reading):
        for entry in meta.get(key, []):
            if len(entry) < 3 or entry[1] != "freq":
                continue
            value = _coerce_freq_value(entry[2])
            if value is None:
                continue
            entry_reading = entry[2].get("reading") if isinstance(entry[2], dict) else None
            if entry_reading is None or entry_reading == reading:
                return value
            if fallback is None:
                fallback = value
    return fallback


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
        def_dirs: list[str],
        pitch_dir: str | None = None,
        freq_dirs: list[str] | None = None,
    ):
        # All entries, plus an index mapping every expression AND reading to the
        # entries that bear it (yomitan queries both the expression and reading
        # indexes). ``dict_index`` is the load order = priority (lower wins ties).
        self._entries: list[_Entry] = []
        self._index: dict[str, list[int]] = {}
        self._dict_names: list[str] = []

        for dict_index, path in enumerate(def_dirs):
            print(f"Loading dictionary: {path}", file=sys.stderr)
            self._load_term_banks(Path(path), dict_index)
            self._dict_names.append(_read_dict_title(Path(path)) or Path(path).name)

        self._pitch_meta: dict[str, list] = {}
        if pitch_dir:
            print(f"Loading pitch accent dictionary: {pitch_dir}", file=sys.stderr)
            try:
                self._pitch_meta = _load_meta_banks(Path(pitch_dir))
            except Exception as e:
                print(f"  WARNING: could not load pitch dict: {e}", file=sys.stderr)

        # (label, meta) per frequency list, kept in load order so the resulting
        # frequency display follows the order the lists were supplied in.
        self._freq_lists: list[tuple[str, dict]] = []
        for path in freq_dirs or []:
            directory = Path(path)
            label = _read_dict_title(directory) or directory.name
            print(f"Loading frequency dictionary: {label} ({path})", file=sys.stderr)
            self._freq_lists.append((label, _load_meta_banks(directory)))

        print(
            f"Dictionaries loaded: {len(self._entries):,} entries "
            f"across {len(def_dirs)} dict(s).",
            file=sys.stderr,
        )

    def _load_term_banks(self, directory: Path, dict_index: int) -> None:
        for fname in _bank_files(directory, "term_bank_"):
            for row in json.loads(fname.read_text(encoding="utf-8")):
                entry = _Entry(
                    expression=row[0],
                    reading=row[1] or row[0],
                    def_tags=row[2] or "",
                    rules=row[3] or "",
                    score=row[4] if isinstance(row[4], (int, float)) else 0,
                    glossary=row[5],
                    dict_index=dict_index,
                )
                idx = len(self._entries)
                self._entries.append(entry)
                self._index.setdefault(entry.expression, []).append(idx)
                if entry.reading != entry.expression:
                    self._index.setdefault(entry.reading, []).append(idx)

    def find_all_terms(self, word: str) -> list[DictResult]:
        """Return all entries at the longest deinflected match, sorted by dict priority."""
        best_per_entry: dict[int, tuple[int, int]] = {}

        source = word
        while source:
            for candidate in JAPANESE_TRANSFORMER.transform(source):
                entry_ids = self._index.get(candidate.text)
                if not entry_ids:
                    continue
                source_len = len(source)
                chain_len = len(candidate.trace)
                for entry_id in entry_ids:
                    entry = self._entries[entry_id]
                    entry_flags = JAPANESE_TRANSFORMER.get_condition_flags_from_parts_of_speech(
                        entry.rules.split()
                    )
                    if not LanguageTransformer.conditions_match(
                        candidate.conditions, entry_flags
                    ):
                        continue
                    prev = best_per_entry.get(entry_id)
                    if prev is None or (source_len, -chain_len) > (prev[0], -prev[1]):
                        best_per_entry[entry_id] = (source_len, chain_len)
            source = source[:-1]

        if not best_per_entry:
            return []

        max_source_len = max(v[0] for v in best_per_entry.values())
        top = [
            (eid, chain_len)
            for eid, (source_len, chain_len) in best_per_entry.items()
            if source_len == max_source_len
        ]
        top.sort(key=lambda x: (
            self._entries[x[0]].dict_index,
            x[1],
            -self._entries[x[0]].score,
        ))
        results = [self._build_result(self._entries[eid]) for eid, _ in top]
        # Stable re-sort: within each dict group, lower alphabet ratio (more Japanese) first.
        results.sort(key=lambda r: (
            self._dict_names.index(r.dict_name),
            _alphabet_ratio(r),
        ))
        return results

    def find_term(self, word: str) -> DictResult | None:
        """Return the single best match (first result of find_all_terms)."""
        results = self.find_all_terms(word)
        return results[0] if results else None

    def _build_result(self, entry: _Entry) -> DictResult:
        definitions = (
            _extract_text(entry.glossary)
            if isinstance(entry.glossary, list)
            else [str(entry.glossary)]
        )
        pos = [t.strip() for t in entry.def_tags.split() if t.strip()]
        pitch_position = self._get_pitch(entry.expression, entry.reading)
        return DictResult(
            expression=entry.expression,
            reading=entry.reading,
            definitions=definitions,
            pos=pos,
            pitch_position=pitch_position,
            pitch_category=_get_pitch_category(pitch_position, entry.reading),
            frequencies=self._get_frequencies(entry.expression, entry.reading),
            dict_name=self._dict_names[entry.dict_index],
        )

    def _get_pitch(self, expression: str, reading: str) -> int | None:
        for key in (expression, reading):
            # Prefer an entry whose reading matches, then fall back to any pitch.
            for require_reading in (True, False):
                for entry in self._pitch_meta.get(key, []):
                    if entry[1] != "pitch":
                        continue
                    data = entry[2]
                    if not isinstance(data, dict):
                        continue
                    pitches = data.get("pitches", [])
                    if not pitches:
                        continue
                    if require_reading and data.get("reading", reading) != reading:
                        continue
                    return pitches[0].get("position")
        return None

    def _get_frequencies(self, expression: str, reading: str) -> list[tuple[str, int]]:
        out: list[tuple[str, int]] = []
        for label, meta in self._freq_lists:
            value = _extract_freq(meta, expression, reading)
            if value is not None:
                out.append((label, value))
        return out


def get_dict(
    def_dirs: list[str],
    pitch_dir: str | None = None,
    freq_dirs: list[str] | None = None,
) -> DictionarySet:
    return DictionarySet(def_dirs, pitch_dir=pitch_dir, freq_dirs=freq_dirs)
