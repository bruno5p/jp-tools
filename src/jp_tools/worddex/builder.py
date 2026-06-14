from pathlib import Path

import pandas as pd

from jp_tools._paths import DEFAULT_DICTS_DIR
from jp_tools.worddex.anki_reader import read_apkg_fields
from jp_tools.worddex.freq_table import build_freq_table
from jp_tools.worddex.tokenizer import extract_sentence_words

_COLUMN_ORDER = [
    "Learned",
    "Anki (word)",
    "Anki (sentence)",
    "Freq JPDB",
    "Freq anime drama",
    "Freq SoL",
    "Freq innocent",
    "Agg Freq Avg",
    "Agg Freq Min Spoken",
    "Agg Freq Min",
]


def build_worddex(
    apkg_path: Path,
    dicts_dir: Path = DEFAULT_DICTS_DIR,
    sentence_field: str = "Sentence",
    expression_field: str = "Expression",
    output_path: Path | None = Path("worddex.csv"),
) -> pd.DataFrame:
    """Build the WordDex and optionally save to CSV.

    The WordDex is indexed by word (from the union of all frequency lists).
    Words from Anki that do not appear in any frequency list are not included —
    the Anki sets only determine the Learned/Anki columns for existing rows.

    Args:
        apkg_path: Path to the exported .apkg file.
        dicts_dir: Directory containing the Yomitan frequency list folders.
        sentence_field: Anki field name holding the example sentence.
        expression_field: Anki field name holding the target word/expression.
        output_path: Where to write the CSV (UTF-8 with BOM for Excel compat).
                     Pass None to skip writing.

    Returns:
        DataFrame indexed by "Word" with Learned, Anki, and frequency columns.
    """
    fields = read_apkg_fields(apkg_path, [sentence_field, expression_field])

    anki_sentence_words = extract_sentence_words(fields.get(sentence_field, []))
    anki_expression_words = {w.strip() for w in fields.get(expression_field, []) if w.strip()}

    df = build_freq_table(dicts_dir)

    df["Anki (sentence)"] = df.index.isin(anki_sentence_words).astype(int)
    df["Anki (word)"] = df.index.isin(anki_expression_words).astype(int)
    df["Learned"] = (
        (df["Anki (sentence)"] + df["Anki (word)"]) > 0
    ).astype(int)

    available_cols = [c for c in _COLUMN_ORDER if c in df.columns]
    df = df[available_cols]

    if output_path is not None:
        df.to_csv(output_path, encoding="utf-8-sig")

    return df
