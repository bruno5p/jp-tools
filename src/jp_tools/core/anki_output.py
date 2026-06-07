import os
import sys
from dataclasses import dataclass

try:
    import genanki
except ImportError:
    sys.exit("Missing dependency: genanki\n  pip install genanki")


MODEL_ID = 1_947_382_910  # stable arbitrary ID
DECK_ID  = 1_947_382_911

_MODEL = genanki.Model(
    MODEL_ID,
    "YomiMining",
    fields=[
        {"name": "Expression"},
        {"name": "Reading"},
        {"name": "Glossary"},
        {"name": "PartOfSpeech"},
        {"name": "Sentence"},
        {"name": "SentenceAudio"},
        {"name": "PitchAccent"},
        {"name": "Frequency"},
    ],
    templates=[
        {
            "name": "Recognition",
            "qfmt": (
                "<div style='font-size:2em;text-align:center'>{{Expression}}</div>"
                "<br>"
                "<div style='text-align:center;color:#888'>{{Sentence}}</div>"
                "{{SentenceAudio}}"
            ),
            "afmt": (
                "{{FrontSide}}<hr>"
                "<div style='text-align:center;font-size:1.4em'>{{Reading}}</div>"
                "<div style='text-align:center'>{{PitchAccent}}</div>"
                "<br>"
                "<div>{{Glossary}}</div>"
                "<br>"
                "<div style='color:#888;font-size:0.85em'>"
                "{{PartOfSpeech}}"
                "{{#Frequency}}&nbsp;·&nbsp;#{{Frequency}}{{/Frequency}}"
                "</div>"
            ),
        }
    ],
    css=(
        ".card{font-family:'Hiragino Sans',Meiryo,sans-serif;font-size:20px;"
        "text-align:left;color:#333;background:#fff;padding:20px}"
        ".pitch{display:inline-block}"
    ),
)


@dataclass
class NoteData:
    expression: str
    reading: str
    glossary: str
    pos: str
    sentence: str
    audio_filename: str
    pitch_html: str
    frequency: str


class AnkiDeck:
    def __init__(self, deck_name: str = "Japanese Mining"):
        self._deck = genanki.Deck(DECK_ID, deck_name)
        self._media: list[str] = []

    def add_note(self, data: NoteData, audio_path: str | None = None) -> None:
        sentence_audio = ""
        if audio_path and os.path.isfile(audio_path):
            filename = os.path.basename(audio_path)
            sentence_audio = f"[sound:{filename}]"
            self._media.append(os.path.abspath(audio_path))
        elif data.audio_filename:
            sentence_audio = f"[sound:{data.audio_filename}]"

        note = genanki.Note(
            model=_MODEL,
            fields=[
                data.expression,
                data.reading,
                data.glossary,
                data.pos,
                data.sentence,
                sentence_audio,
                data.pitch_html,
                data.frequency,
            ],
        )
        self._deck.add_note(note)

    def flush(self, output_path: str) -> None:
        package = genanki.Package(self._deck)
        package.media_files = self._media
        package.write_to_file(output_path)
        print(f"Wrote {len(self._deck.notes)} note(s) to: {output_path}")
