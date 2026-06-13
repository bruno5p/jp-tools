import hashlib
import os
import re
import sys
import tempfile
import genanki
from dataclasses import dataclass
from ._lapis_template import CARD_CSS, RECOGNITION_AFMT, RECOGNITION_QFMT
from ..lookup import DictResult
from .._paths import DEFAULT_DICTS_DIR


# Frequency lists shown on each card, in display order. Each is a folder of
# extracted Yomitan frequency banks under dicts/; missing ones are skipped.
_DEFAULT_FREQ_DIRS = (
    "jpdb_freq",
    "anime_drama_freq_list",
    "innocent_ranked",
    "SoL Top 100",
)


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
        freqs: list[str] | None = None,
        word_audio: bool = True,
        audio_sources=None,
        audio_timeout: float = 10,
    ):
        deck_id = self._stable_id(f"jp-tools:deck:{deck_name}")
        self._deck = genanki.Deck(deck_id, deck_name)
        self._media: list[str] = []
        self._daijirin = daijirin or str(DEFAULT_DICTS_DIR / "daijirin")
        self._daijisen = daijisen or str(DEFAULT_DICTS_DIR / "daijisen")
        self._jmdict = jmdict or str(DEFAULT_DICTS_DIR / "jmdict_english")
        self._pitch = pitch or str(DEFAULT_DICTS_DIR / "pitch_daijisen")
        self._freqs = freqs or [
            str(DEFAULT_DICTS_DIR / name) for name in _DEFAULT_FREQ_DIRS
        ]
        self._dict_set = None
        self._word_audio = word_audio
        self._audio_sources = audio_sources
        self._audio_timeout = audio_timeout
        self._audio = None  # lazily created AudioDownloader

    @staticmethod
    def _stable_id(seed: str) -> int:
        """Derive a stable positive 63-bit integer from a string seed."""
        digest = hashlib.sha256(seed.encode()).digest()
        return int.from_bytes(digest[:8], "big") & 0x7FFF_FFFF_FFFF_FFFF

    @staticmethod
    def _opt_path(path: str | None) -> str | None:
        return path if path and os.path.isdir(path) else None

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
            pitch_dir=self._opt_path(self._pitch),
            freq_dirs=[p for p in self._freqs if os.path.isdir(p)],
        )

    @staticmethod
    def _strip_links(text: str) -> str:
        # Preserve inner text of complete <a>…</a> pairs
        text = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", text, flags=re.DOTALL)
        # Strip all remaining tags except <br>
        text = re.sub(r"<(?!br\b)/?[^>]+>", "", text, flags=re.IGNORECASE)
        return text

    def _format_entries(self, results: list[DictResult]) -> str:
        """Format DictResults as yomitan-style HTML for Anki Glossary / MainDefinition fields."""
        items = []
        for r in results:
            label = ", ".join(r.pos) + ", " + r.dict_name if r.pos else r.dict_name
            defs = "<br>".join(self._strip_links(d) for d in r.definitions)
            items.append(
                f'<li data-dictionary="{r.dict_name}"><i>({label})</i> {defs}</li>'
            )
        return (
            '<div style="text-align: left;" class="yomitan-glossary">'
            "<ol>" + "".join(items) + "</ol>"
            "</div>"
        )

    def _get_audio(self):
        """Lazily build the AudioDownloader with a creator-owned media dir."""
        if self._audio is None:
            from .audio import DEFAULT_SOURCES, AudioDownloader

            media_dir = tempfile.mkdtemp(prefix="jp_audio_")
            self._audio = AudioDownloader(
                sources=self._audio_sources or DEFAULT_SOURCES,
                media_dir=media_dir,
                timeout=self._audio_timeout,
            )
        return self._audio

    def add_word(
        self,
        word: str,
        sentence: str,
        audio: str,
        *,
        word_audio_path: str | None = None,
        picture: str | None = None,
        hint: str | None = None,
        definition_override: str | None = None,
        definition_picture: str | None = None,
        tags: str | None = None,
    ) -> str:
        """Look up word, build a note, and add it to the deck. Returns a log line."""
        from ..furigana import get_furigana_plain, get_sentence_furigana

        if self._dict_set is None:
            self._load_dicts()

        # Yomitan-style lookup: deinflect the surface word and match against the
        # dictionaries. The sentence is used only for card building, not lookup.
        results = self._dict_set.find_all_terms(word)

        expression_audio = ""
        audio_ok = False
        if not results:
            print(f"  WARNING: '{word}' not found in dictionary — using surface form")
            expression_reading = word
            expression_furigana = word
            main_definition = "(not found)"
            glossary = "(not found)"
            pitch_position = ""
            pitch_categories = ""
            frequency = ""
            freq_sort = ""
        else:
            top = results[0]
            expression_reading = top.reading
            expression_furigana = get_furigana_plain(word, top.reading)
            pitch_position = (
                str(top.pitch_position) if top.pitch_position is not None else ""
            )
            pitch_categories = top.pitch_category or ""
            # "JPDB: 9892, Anime & J-drama: 14718, …" — the card template's JS
            # splits this on commas to render one bullet per list. Lists missing
            # the word are already absent from result.frequencies.
            frequency = (
                (
                    '<ul style="text-align: left;">'
                    + "".join(
                        f"<li>{label}: {rank}</li>" for label, rank in top.frequencies
                    )
                    + "</ul>"
                )
                if top.frequencies
                else ""
            )
            # Headline/sort value: the first (primary) list's rank, e.g. JPDB.
            freq_sort = str(top.frequencies[0][1]) if top.frequencies else ""

            top_dict = top.dict_name
            main_definition = self._format_entries(
                [r for r in results if r.dict_name == top_dict]
            )
            glossary = self._format_entries(results)

            # Yomitan-style word audio for the dictionary headword. Fail-soft:
            # an unreachable source just leaves ExpressionAudio empty.
            if self._word_audio:
                path = self._get_audio().fetch(top.expression, top.reading)
                if path:
                    expression_audio = f"[sound:{os.path.basename(path)}]"
                    self._media.append(path)
                    audio_ok = True

        # Explicit word_audio_path overrides auto-fetch (e.g. pre-recorded audio).
        if word_audio_path and os.path.isfile(word_audio_path):
            expression_audio = f"[sound:{os.path.basename(word_audio_path)}]"
            self._media.append(os.path.abspath(word_audio_path))
            audio_ok = True

        # Explicit definition overrides dictionary lookup (pitch/freq still auto).
        if definition_override:
            main_definition = definition_override

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
            expression_audio=expression_audio,
            selection_text=word,
            main_definition=main_definition,
            sentence=bolded,
            sentence_furigana=sentence_furigana,
            sentence_audio="",
            glossary=glossary,
            pitch_position=pitch_position,
            pitch_categories=pitch_categories,
            frequency=frequency,
            freq_sort=freq_sort,
            misc_info="",
        )
        self.add_note(
            data,
            audio_path=audio if audio else None,
            picture=picture,
            hint=hint,
            definition_picture=definition_picture,
            tags=tags,
        )
        audio_flag = "✓" if audio_ok else ("✗" if self._word_audio else "-")
        return (
            f"  + {word}  [{expression_reading}]"
            f"  pitch={pitch_position or '-'}({pitch_categories or '-'})"
            f"  freq={frequency or '-'}"
            f"  audio={audio_flag}"
        )

    def add_note(
        self,
        data: NoteData,
        audio_path: str | None = None,
        picture: str | None = None,
        hint: str | None = None,
        definition_picture: str | None = None,
        tags: str | None = None,
    ) -> None:
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
                "",
                data.main_definition,
                definition_picture or "",  # DefinitionPicture
                data.sentence,
                data.sentence_furigana,
                sentence_audio,  # SentenceAudio from audio_path
                picture or "",  # Picture
                data.glossary,
                hint or "",  # Hint
                "",  # IsWordAndSentenceCard
                "",  # IsClickCard
                "1",  # IsSentenceCard
                data.pitch_position,
                data.pitch_categories,
                data.frequency,
                data.freq_sort,
                data.misc_info,
            ],
            tags=[t.strip() for t in tags.split(",") if t.strip()] if tags else [],
        )
        self._deck.add_note(note)

    def flush(self, output_path: str) -> None:
        package = genanki.Package(self._deck)
        package.media_files = self._media
        package.write_to_file(output_path)
        print(f"Wrote {len(self._deck.notes)} note(s) to: {output_path}")
