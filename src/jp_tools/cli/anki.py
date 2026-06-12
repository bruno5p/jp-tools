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
    parser.add_argument("--daijirin", default=None, metavar="ZIP",
                        help="三省堂スーパー大辞林 ZIP (default: dicts/daijirin.zip)")
    parser.add_argument("--daijisen", default=None, metavar="ZIP",
                        help="大辞泉 ZIP (default: dicts/daijisen.zip)")
    parser.add_argument("--jmdict", default=None, metavar="ZIP",
                        help="JMdict English ZIP fallback (default: dicts/jmdict_english.zip)")
    parser.add_argument("--pitch", default=None, metavar="ZIP",
                        help="Pitch accent ZIP (default: dicts/pitch_daijisen.zip)")
    parser.add_argument("--freq", default=None, metavar="ZIP",
                        help="Frequency list ZIP (default: dicts/jpdb_freq.zip)")
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
