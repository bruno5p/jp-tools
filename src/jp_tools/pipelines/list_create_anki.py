"""ListCreateAnkiPipeline: word/sentence CSV → Anki deck (.apkg).

Reads a CSV (columns: video_url, timestamp, word, sentence, ref_audio_path —
e.g. the output of :class:`YoutubeTranscribePipeline`) and creates one Anki note
per row using Yomitan-format dictionary data.
"""

import csv
import os

from .._paths import DEFAULT_DICTS_DIR
from .base import Pipeline


def _opt_path(path: str | None) -> str | None:
    return path if path and os.path.isfile(path) else None


class ListCreateAnkiPipeline(Pipeline):
    """Build an Anki .apkg deck from a word list CSV."""

    def __init__(
        self,
        csv_path: str,
        output: str = "deck.apkg",
        deck_name: str = "Japanese Mining",
        jmdict: str | None = None,
        kanjium: str | None = None,
        freq: str | None = None,
    ):
        self.csv_path = csv_path
        self.output = output
        self.deck_name = deck_name
        self.jmdict = jmdict or str(DEFAULT_DICTS_DIR / "jitendex.zip")
        self.kanjium = kanjium or str(DEFAULT_DICTS_DIR / "kanjium_pitch_accents.zip")
        self.freq = freq or str(DEFAULT_DICTS_DIR / "jpdb_v2.2_freq.zip")

    def _process_row(self, row: dict, dict_set, deck) -> None:
        from ..core.anki_output import NoteData
        from ..core.morphology import get_dictionary_form
        from ..core.pitch_renderer import render_pitch_html

        word = row.get("word", "").strip()
        sentence = row.get("sentence", "").strip()
        audio = row.get("ref_audio_path", "").strip()

        if not word:
            print("  SKIP: empty word")
            return

        lemma = get_dictionary_form(sentence, word) if sentence else word
        result = dict_set.lookup(lemma)

        if result is None:
            print(f"  WARNING: '{lemma}' not found in dictionary — using surface form")
            reading = word
            glossary = "(not found)"
            pos = ""
            pitch_html = word
            frequency = ""
        else:
            reading = result.reading
            glossary = "<br>".join(result.definitions) if result.definitions else "(no definition)"
            pos = " ".join(result.pos)
            pitch_html = render_pitch_html(reading, result.pitch_position)
            frequency = str(result.frequency) if result.frequency is not None else ""

        data = NoteData(
            expression=word,
            reading=reading,
            glossary=glossary,
            pos=pos,
            sentence=sentence,
            audio_filename=os.path.basename(audio) if audio else "",
            pitch_html=pitch_html,
            frequency=frequency,
        )
        deck.add_note(data, audio_path=audio if audio else None)
        print(f"  + {word}  [{reading}]  pitch={result.pitch_position if result else '-'}  freq={frequency or '-'}")

    def run(self) -> str:
        from ..core.anki_output import AnkiDeck
        from ..core.dict_loader import get_dict

        if not os.path.isfile(self.csv_path):
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")
        if not os.path.isfile(self.jmdict):
            raise FileNotFoundError(
                f"JMdict ZIP not found: {self.jmdict}\n"
                "  Download Jitendex from https://github.com/stephenmk/Jitendex/releases\n"
                "  and place it in the dicts/ folder (or pass jmdict=<path>)."
            )

        dict_set = get_dict(
            self.jmdict,
            kanjium_zip=_opt_path(self.kanjium),
            freq_zip=_opt_path(self.freq),
        )
        deck = AnkiDeck(self.deck_name)

        with open(self.csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        if not rows:
            raise ValueError("CSV has no data rows.")

        errors = []
        for i, row in enumerate(rows, 1):
            word = row.get("word", "").strip()
            print(f"[{i}/{len(rows)}] {word}")
            try:
                self._process_row(row, dict_set, deck)
            except Exception as e:
                print(f"  ERROR: {e}")
                errors.append(word)

        deck.flush(self.output)

        if errors:
            print(f"\nFailed words: {errors}")
        return self.output
