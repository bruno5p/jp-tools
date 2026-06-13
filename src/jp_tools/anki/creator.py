import hashlib
import os
import sys
from dataclasses import dataclass

try:
    import genanki
except ImportError:
    sys.exit("Missing dependency: genanki\n  pip install genanki")

from .._paths import DEFAULT_DICTS_DIR


def _opt_path(path: str | None) -> str | None:
    return path if path and os.path.isdir(path) else None


from ._lapis_template import CARD_CSS, RECOGNITION_AFMT, RECOGNITION_QFMT

# This ID was the original value chosen to match the "Lapis" note type already
# present in the target Anki collection.  Do not change it without also
# migrating existing notes.
_MODEL_ID = 1667218449922


_MODEL = genanki.Model(
    _MODEL_ID,
    "Lapis",
    fields=[
        {"name": "Expression"},
        {"name": "ExpressionFurigana"},
        {"name": "ExpressionReading"},
        {"name": "ExpressionAudio"},
        {"name": "SelectionText"},
        {"name": "MainDefinition"},
        {"name": "DefinitionPicture"},
        {"name": "Sentence"},
        {"name": "SentenceFurigana"},
        {"name": "SentenceAudio"},
        {"name": "Picture"},
        {"name": "Glossary"},
        {"name": "Hint"},
        {"name": "IsWordAndSentenceCard"},
        {"name": "IsClickCard"},
        {"name": "IsSentenceCard"},
        {"name": "PitchPosition"},
        {"name": "PitchCategories"},
        {"name": "Frequency"},
        {"name": "FreqSort"},
        {"name": "MiscInfo"},
    ],
    templates=[
        {
            "name": "Mining",
            "qfmt": RECOGNITION_QFMT,
            "afmt": RECOGNITION_AFMT,
        }
    ],
    css=CARD_CSS,
)
# genanki infers required fields by running Mustache over the qfmt.  Our
# template is Anki JS, not plain Mustache, so the inference picks the wrong
# fields (Hint / IsClickCard) and generates zero cards.  Override _req to
# declare Expression (index 0) as the sole required field.
_MODEL._req = [[0, "any", [0]]]


@dataclass
class NoteData:
    expression: str
    expression_furigana: str
    expression_reading: str
    expression_audio: str
    selection_text: str
    main_definition: str
    sentence: str
    sentence_furigana: str
    sentence_audio: str
    glossary: str
    pitch_position: str
    pitch_categories: str
    frequency: str
    freq_sort: str
    misc_info: str


class AnkiCardCreator:
    def __init__(
        self,
        deck_name: str = "Test",
        daijirin: str | None = None,
        daijisen: str | None = None,
        jmdict: str | None = None,
        pitch: str | None = None,
        freq: str | None = None,
    ):
        deck_id = self._stable_id(f"jp-tools:deck:{deck_name}")
        self._deck = genanki.Deck(deck_id, deck_name)
        self._media: list[str] = []
        self._daijirin = daijirin or str(DEFAULT_DICTS_DIR / "daijirin")
        self._daijisen = daijisen or str(DEFAULT_DICTS_DIR / "daijisen")
        self._jmdict = jmdict or str(DEFAULT_DICTS_DIR / "jmdict_english")
        self._pitch = pitch or str(DEFAULT_DICTS_DIR / "pitch_daijisen")
        self._freq = freq or str(DEFAULT_DICTS_DIR / "jpdb_freq")
        self._dict_set = None

    @staticmethod
    def _stable_id(seed: str) -> int:
        """Derive a stable positive 63-bit integer from a string seed."""
        digest = hashlib.sha256(seed.encode()).digest()
        return int.from_bytes(digest[:8], "big") & 0x7FFF_FFFF_FFFF_FFFF

    def _load_dicts(self):
        from ..lookup import get_dict

        def_dirs = [
            p
            for p in [self._daijirin, self._daijisen, self._jmdict]
            if os.path.isdir(p)
        ]
        if not def_dirs:
            raise FileNotFoundError(
                f"No definition dictionaries found in {DEFAULT_DICTS_DIR}.\n"
                "  Expected folders: daijirin/, daijisen/, or jmdict_english/"
            )
        self._dict_set = get_dict(
            def_dirs,
            pitch_dir=_opt_path(self._pitch),
            freq_dir=_opt_path(self._freq),
        )

    def add_word(self, word: str, sentence: str, audio: str) -> str:
        """Look up word, build a note, and add it to the deck. Returns a log line."""
        from ..furigana import get_furigana_plain, get_sentence_furigana

        if self._dict_set is None:
            self._load_dicts()

        # Yomitan-style lookup: deinflect the surface word and match against the
        # dictionaries. The sentence is used only for card building, not lookup.
        result = self._dict_set.find_term(word)

        if result is None:
            print(f"  WARNING: '{word}' not found in dictionary — using surface form")
            expression_reading = word
            expression_furigana = word
            main_definition = "(not found)"
            glossary = "(not found)"
            pitch_position = ""
            pitch_categories = ""
            frequency = ""
        else:
            expression_reading = result.reading
            expression_furigana = get_furigana_plain(word, result.reading)
            main_definition = (
                result.definitions[0] if result.definitions else "(no definition)"
            )
            glossary = (
                "<br>".join(result.definitions)
                if result.definitions
                else "(no definition)"
            )
            pitch_position = (
                str(result.pitch_position) if result.pitch_position is not None else ""
            )
            pitch_categories = result.pitch_category or ""
            frequency = str(result.frequency) if result.frequency is not None else ""

        if sentence and word in sentence:
            idx = sentence.index(word)
            bolded = sentence[:idx] + f"<b>{word}</b>" + sentence[idx + len(word) :]
        else:
            bolded = sentence

        sentence_furigana = get_sentence_furigana(sentence) if sentence else ""

        data = NoteData(
            expression=word,
            expression_furigana=expression_furigana,
            expression_reading=expression_reading,
            expression_audio="",
            selection_text=word,
            main_definition=main_definition,
            sentence=bolded,
            sentence_furigana=sentence_furigana,
            sentence_audio="",
            glossary=glossary,
            pitch_position=pitch_position,
            pitch_categories=pitch_categories,
            frequency=frequency,
            freq_sort=frequency,
            misc_info="",
        )
        self.add_note(data, audio_path=audio if audio else None)
        return (
            f"  + {word}  [{expression_reading}]"
            f"  pitch={pitch_position or '-'}({pitch_categories or '-'})"
            f"  freq={frequency or '-'}"
        )

    def add_note(self, data: NoteData, audio_path: str | None = None) -> None:
        sentence_audio = ""
        if audio_path and os.path.isfile(audio_path):
            filename = os.path.basename(audio_path)
            sentence_audio = f"[sound:{filename}]"
            self._media.append(os.path.abspath(audio_path))

        note = genanki.Note(
            model=_MODEL,
            fields=[
                data.expression,
                data.expression_furigana,
                data.expression_reading,
                data.expression_audio,
                data.selection_text,
                data.main_definition,
                "",  # DefinitionPicture
                data.sentence,
                data.sentence_furigana,
                sentence_audio,  # SentenceAudio from audio_path
                "",  # Picture
                data.glossary,
                "",  # Hint
                "",  # IsWordAndSentenceCard
                "",  # IsClickCard
                "1",  # IsSentenceCard
                data.pitch_position,
                data.pitch_categories,
                data.frequency,
                data.freq_sort,
                data.misc_info,
            ],
        )
        self._deck.add_note(note)

    def flush(self, output_path: str) -> None:
        package = genanki.Package(self._deck)
        package.media_files = self._media
        package.write_to_file(output_path)
        print(f"Wrote {len(self._deck.notes)} note(s) to: {output_path}")
