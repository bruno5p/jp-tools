"""Pure-Python port of yomitan's ``LanguageTransformer``.

Mirrors ``ext/js/language/language-transformer.js`` from the yomitan repository.
Given a *condition descriptor* and a set of *transforms*, it deinflects a source
string into every candidate base form reachable by chaining the transform rules,
tracking the grammatical ``conditions`` (a bitfield) and the ``trace`` of rules
applied along the way.

No external dependencies — this module can be imported and tested without the
dictionary data or fugashi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

# A rule as supplied to ``add_descriptor``: a compiled "is inflected" matcher, a
# deinflect function, and the input/output condition *names* (resolved to flags
# during registration).
RawRule = tuple["re.Pattern[str]", Callable[[str], str], list[str], list[str]]


@dataclass(frozen=True)
class _Rule:
    is_inflected: "re.Pattern[str]"
    deinflect: Callable[[str], str]
    conditions_in: int
    conditions_out: int


@dataclass(frozen=True)
class _Transform:
    id: str
    name: str
    rules: tuple[_Rule, ...]


@dataclass(frozen=True)
class TraceFrame:
    transform: str
    rule_index: int
    text: str


@dataclass(frozen=True)
class TransformedText:
    text: str
    conditions: int
    trace: tuple[TraceFrame, ...]


class LanguageTransformer:
    def __init__(self) -> None:
        self._next_flag_index = 0
        self._transforms: list[_Transform] = []
        self._condition_type_to_flags: dict[str, int] = {}
        self._pos_to_flags: dict[str, int] = {}

    def add_descriptor(self, conditions: dict, transforms: dict) -> None:
        """Register a descriptor.

        ``conditions`` maps a condition name to ``{"isDictionaryForm": bool,
        "subConditions": list[str] | None}``. ``transforms`` maps a transform id
        to ``{"name": str, "rules": list[RawRule]}``.
        """
        flags_map, next_index = self._build_condition_flags(
            conditions, self._next_flag_index
        )

        built: list[_Transform] = []
        for tid, transform in transforms.items():
            rules: list[_Rule] = []
            for is_inflected, deinflect, conditions_in, conditions_out in transform["rules"]:
                flags_in = self._flags_strict(flags_map, conditions_in)
                flags_out = self._flags_strict(flags_map, conditions_out)
                if flags_in is None or flags_out is None:
                    raise ValueError(f"Invalid conditions for transform {tid!r}")
                rules.append(_Rule(is_inflected, deinflect, flags_in, flags_out))
            built.append(_Transform(tid, transform["name"], tuple(rules)))

        self._next_flag_index = next_index
        self._transforms.extend(built)

        for ctype, condition in conditions.items():
            flags = flags_map.get(ctype)
            if flags is None:
                continue
            self._condition_type_to_flags[ctype] = flags
            if condition.get("isDictionaryForm"):
                self._pos_to_flags[ctype] = flags

    def transform(self, source_text: str) -> list[TransformedText]:
        """Return every deinflection reachable from ``source_text`` (incl. itself)."""
        results = [TransformedText(source_text, 0, ())]
        i = 0
        while i < len(results):
            text, conditions, trace = (
                results[i].text,
                results[i].conditions,
                results[i].trace,
            )
            for transform in self._transforms:
                for j, rule in enumerate(transform.rules):
                    if not self.conditions_match(conditions, rule.conditions_in):
                        continue
                    if not rule.is_inflected.search(text):
                        continue
                    is_cycle = any(
                        f.transform == transform.id and f.rule_index == j and f.text == text
                        for f in trace
                    )
                    if is_cycle:
                        continue
                    results.append(
                        TransformedText(
                            rule.deinflect(text),
                            rule.conditions_out,
                            (TraceFrame(transform.id, j, text), *trace),
                        )
                    )
            i += 1
        return results

    def get_condition_flags_from_parts_of_speech(self, parts_of_speech: list[str]) -> int:
        """Resolve a term's space-separated ``rules`` field into a condition bitfield.

        Only conditions flagged ``isDictionaryForm`` participate; unknown tags
        contribute nothing (flag 0).
        """
        flags = 0
        for part in parts_of_speech:
            flags |= self._pos_to_flags.get(part, 0)
        return flags

    @staticmethod
    def conditions_match(current_conditions: int, next_conditions: int) -> bool:
        """``True`` if ``current`` is 0 (uninflected), else if they share a bit."""
        return current_conditions == 0 or (current_conditions & next_conditions) != 0

    @staticmethod
    def _flags_strict(flags_map: dict[str, int], condition_types: list[str]) -> int | None:
        flags = 0
        for condition_type in condition_types:
            if condition_type not in flags_map:
                return None
            flags |= flags_map[condition_type]
        return flags

    def _build_condition_flags(
        self, conditions: dict, next_flag_index: int
    ) -> tuple[dict[str, int], int]:
        flags_map: dict[str, int] = {}
        targets = list(conditions.items())
        while targets:
            next_targets = []
            for ctype, condition in targets:
                sub_conditions = condition.get("subConditions")
                if sub_conditions is None:
                    if next_flag_index >= 32:
                        raise ValueError("Maximum number of conditions was exceeded")
                    flags = 1 << next_flag_index
                    next_flag_index += 1
                else:
                    multi = self._flags_strict(flags_map, sub_conditions)
                    if multi is None:
                        next_targets.append((ctype, condition))
                        continue
                    flags = multi
                flags_map[ctype] = flags
            if len(next_targets) == len(targets):
                raise ValueError("Cycle in subCondition declaration")
            targets = next_targets
        return flags_map, next_flag_index
