"""PipelineAnkiFromList: AnkiCardData CSV → Anki deck (.apkg)."""

import csv
import os

from .base import Pipeline
from .models import AnkiCardData


class PipelineAnkiFromList(Pipeline):
    """Build an Anki .apkg deck from an AnkiCardData CSV."""

    def __init__(
        self,
        csv_path: str,
        output: str = "deck.apkg",
        deck_name: str = "Test",
        daijirin: str | None = None,
        daijisen: str | None = None,
        jmdict: str | None = None,
        pitch: str | None = None,
        freqs: list[str] | None = None,
        word_audio: bool = True,
        audio_timeout: float = 10,
    ):
        self.csv_path = csv_path
        self.output = output
        self.deck_name = deck_name
        self._daijirin = daijirin
        self._daijisen = daijisen
        self._jmdict = jmdict
        self._pitch = pitch
        self._freqs = freqs
        self._word_audio = word_audio
        self._audio_timeout = audio_timeout

    def run(self) -> str:
        from ..anki.creator import AnkiCardCreator

        if not os.path.isfile(self.csv_path):
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")

        creator = AnkiCardCreator(
            deck_name=self.deck_name,
            daijirin=self._daijirin,
            daijisen=self._daijisen,
            jmdict=self._jmdict,
            pitch=self._pitch,
            freqs=self._freqs,
            word_audio=self._word_audio,
            audio_timeout=self._audio_timeout,
        )

        with open(self.csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        if not rows:
            raise ValueError("CSV has no data rows.")

        errors = []
        for i, row in enumerate(rows, 1):
            try:
                card = AnkiCardData.from_csv_row(row)
            except Exception as e:
                print(f"[{i}] SKIP: invalid row — {e}")
                continue

            print(f"[{i}/{len(rows)}] {card.word}")
            if not card.word:
                print("  SKIP: empty word")
                continue

            try:
                log = creator.add_word(
                    word=card.word,
                    sentence=card.sentence or "",
                    audio=card.sentence_audio_path or "",
                    word_audio_path=card.word_audio_path,
                    picture=card.picture_path,
                    hint=card.hint,
                    definition_override=card.definition,
                    definition_picture=card.definition_picture_path,
                    tags=card.tags,
                )
                print(log)
            except Exception as e:
                print(f"  ERROR: {e}")
                errors.append(card.word)

        creator.flush(self.output)

        if errors:
            print(f"\nFailed words: {errors}")
        return self.output
