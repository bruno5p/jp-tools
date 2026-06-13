"""Console entry point for the Anki deck builder (jp-anki).

CSV (word/sentence/audio) → Anki deck (.apkg).
"""

import argparse

from ..pipelines import PipelineAnkiFromList


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an Anki .apkg deck from a word list CSV."
    )
    parser.add_argument("csv", help="Input CSV file (e.g. output of jp-pipeline)")
    parser.add_argument("--output", "-o", default="deck.apkg",
                        help="Output .apkg path (default: deck.apkg)")
    parser.add_argument("--deck", "-d", default="Japanese Mining", help="Anki deck name")
    parser.add_argument("--daijirin", default=None, metavar="DIR",
                        help="三省堂スーパー大辞林 folder (default: dicts/daijirin)")
    parser.add_argument("--daijisen", default=None, metavar="DIR",
                        help="大辞泉 folder (default: dicts/daijisen)")
    parser.add_argument("--jmdict", default=None, metavar="DIR",
                        help="JMdict English folder fallback (default: dicts/jmdict_english)")
    parser.add_argument("--pitch", default=None, metavar="DIR",
                        help="Pitch accent folder (default: dicts/pitch_daijisen)")
    parser.add_argument("--freq", nargs="*", default=None, metavar="DIR",
                        help="Frequency list folders shown on each card (default: "
                             "dicts/jpdb_freq, anime_drama_freq_list, innocent_ranked, "
                             "'SoL Top 100')")
    parser.add_argument("--no-word-audio", dest="word_audio", action="store_false",
                        help="Disable automatic word-audio fetching (Yomitan-style: "
                             "local audio server → jpod101 → jisho)")
    parser.add_argument("--audio-timeout", type=float, default=10, metavar="SECONDS",
                        help="Per-request timeout for audio fetching (default: 10)")
    args = parser.parse_args()

    PipelineAnkiFromList(
        args.csv,
        output=args.output,
        deck_name=args.deck,
        daijirin=args.daijirin,
        daijisen=args.daijisen,
        jmdict=args.jmdict,
        pitch=args.pitch,
        freqs=args.freq,
        word_audio=args.word_audio,
        audio_timeout=args.audio_timeout,
    ).run()


if __name__ == "__main__":
    main()
