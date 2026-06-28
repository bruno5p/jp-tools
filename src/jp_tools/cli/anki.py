"""Console entry point for the Anki deck builder (jp-anki).

CSV (word/sentence/audio) → Anki deck (.apkg).
"""

import argparse
from pathlib import Path

from ..config import (
    DEFAULT_DICT_NAMES,
    DEFAULT_FREQ_NAMES,
    DEFAULT_PITCH_NAME,
    load_config,
    resolve_anki,
    resolve_dicts,
)
from ..pipelines import PipelineAnkiFromList


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an Anki .apkg deck from a word list CSV."
    )
    parser.add_argument("csv", help="Input CSV file (e.g. output of jp-pipeline)")
    parser.add_argument("--config", metavar="PATH",
                        help="Path to jp-tools.toml (default: auto-discover)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output .apkg path (default: deck.apkg)")
    parser.add_argument("--deck", "-d", default=None,
                        help="Anki deck name (default: Japanese Mining)")
    parser.add_argument("--dicts-dir", default=None, metavar="DIR",
                        help="Base directory containing all dict folders (default: dicts/)")
    parser.add_argument("--dict-names", nargs="*", default=None, metavar="NAME",
                        help="Definition dict folder names in priority order "
                             f"(default: {' '.join(DEFAULT_DICT_NAMES)})")
    parser.add_argument("--pitch-name", default=None, metavar="NAME",
                        help=f"Pitch accent dict folder name (default: {DEFAULT_PITCH_NAME})")
    parser.add_argument("--freq-names", nargs="*", default=None, metavar="NAME",
                        help="Frequency list folder names "
                             f"(default: {' '.join(DEFAULT_FREQ_NAMES)})")
    parser.add_argument("--no-word-audio", dest="word_audio", action="store_false",
                        default=None,
                        help="Disable automatic word-audio fetching (Yomitan-style: "
                             "local audio server → jpod101 → jisho)")
    parser.add_argument("--audio-timeout", type=float, default=None, metavar="SECONDS",
                        help="Per-request timeout for audio fetching (default: 10)")
    args = parser.parse_args()

    cfg = load_config(Path(args.config) if args.config else None)
    anki = resolve_anki(args, cfg)
    dicts = resolve_dicts(args, cfg)

    PipelineAnkiFromList(
        args.csv,
        output=anki["output"],
        deck_name=anki["deck_name"],
        dicts_dir=dicts["dicts_dir"],
        dict_names=dicts["dict_names"],
        pitch_name=dicts["pitch_name"],
        freq_names=dicts["freq_names"],
        word_audio=anki["word_audio"],
        audio_timeout=anki["audio_timeout"],
    ).run()


if __name__ == "__main__":
    main()
