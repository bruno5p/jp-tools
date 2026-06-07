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
    parser.add_argument("--jmdict", default=None, metavar="ZIP",
                        help="Jitendex/JMdict ZIP (default: dicts/jitendex.zip)")
    parser.add_argument("--kanjium", default=None, metavar="ZIP",
                        help="Kanjium pitch accent ZIP (default: dicts/kanjium_pitch_accents.zip)")
    parser.add_argument("--freq", default=None, metavar="ZIP",
                        help="Frequency list ZIP (default: dicts/jpdb_v2.2_freq.zip)")
    args = parser.parse_args()

    ListCreateAnkiPipeline(
        args.csv,
        output=args.output,
        deck_name=args.deck,
        jmdict=args.jmdict,
        kanjium=args.kanjium,
        freq=args.freq,
    ).run()


if __name__ == "__main__":
    main()
