"""Console entry point for the Anki deck builder (jp-anki).

CSV (word/sentence/audio) → Anki deck (.apkg).
"""

import argparse

from ..pipelines import ListCreateAnkiPipeline


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
    parser.add_argument("--freq", default=None, metavar="DIR",
                        help="Frequency list folder (default: dicts/jpdb_freq)")
    args = parser.parse_args()

    ListCreateAnkiPipeline(
        args.csv,
        output=args.output,
        deck_name=args.deck,
        daijirin=args.daijirin,
        daijisen=args.daijisen,
        jmdict=args.jmdict,
        pitch=args.pitch,
        freq=args.freq,
    ).run()


if __name__ == "__main__":
    main()
