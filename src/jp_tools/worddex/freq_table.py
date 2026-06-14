from pathlib import Path

import pandas as pd

from jp_tools.lookup.dictionary import _coerce_freq_value, _load_meta_banks

FREQ_LISTS: dict[str, str] = {
    "Freq JPDB": "jpdb_freq",
    "Freq anime drama": "anime_drama_freq_list",
    "Freq SoL": "SoL Top 100",
    "Freq innocent": "innocent_ranked",
}

_SPOKEN_COLS = ["Freq anime drama", "Freq SoL"]


def _is_kana_freq(data) -> bool:
    """Return True if this JPDB entry is a kana-form frequency (marked with ㋕).

    JPDB emits two entries for kanji words that share a kana reading: one for
    the kana form (e.g. こと=14, marked ㋕) and one for the specific kanji
    (e.g. 事=193, unmarked). We prefer the kanji-specific rank.
    """
    if not isinstance(data, dict):
        return False
    display = data.get("displayValue") or ""
    if not display:
        freq = data.get("frequency")
        if isinstance(freq, dict):
            display = freq.get("displayValue") or ""
    return "㋕" in display


def _meta_to_series(meta: dict, col_name: str) -> pd.Series:
    """Convert a Yomitan meta bank dict to a word→rank Series.

    For JPDB entries that carry both a kana-form rank (㋕) and a kanji-specific
    rank, the kanji-specific rank is used. The kana rank is only kept as a
    fallback when no kanji-specific entry exists.
    """
    data: dict[str, int] = {}
    kana_fallback: dict[str, int] = {}
    for word, entries in meta.items():
        for entry in entries:
            if len(entry) < 3 or entry[1] != "freq":
                continue
            rank = _coerce_freq_value(entry[2])
            if rank is None:
                continue
            if _is_kana_freq(entry[2]):
                if word not in kana_fallback or rank < kana_fallback[word]:
                    kana_fallback[word] = rank
            else:
                if word not in data or rank < data[word]:
                    data[word] = rank
    # Fill in words that only appear in kana-marked entries
    for word, rank in kana_fallback.items():
        if word not in data:
            data[word] = rank
    return pd.Series(data, name=col_name, dtype="float64")


def build_freq_table(dicts_dir: Path) -> pd.DataFrame:
    """Return a DataFrame indexed by word with frequency columns and aggregates.

    Rows are the union of all words appearing in any of the four frequency
    lists (JPDB, anime drama, SoL, innocent). Missing values are NaN.
    Aggregate columns use lower-is-better rank semantics (min = most frequent).
    """
    series_list: list[pd.Series] = []
    for col_name, dir_name in FREQ_LISTS.items():
        dir_path = dicts_dir / dir_name
        if not dir_path.is_dir():
            print(f"Warning: frequency list directory not found: {dir_path}")
            continue
        meta = _load_meta_banks(dir_path)
        series_list.append(_meta_to_series(meta, col_name))

    if not series_list:
        raise FileNotFoundError(
            f"No frequency list directories found under: {dicts_dir}"
        )

    df = pd.concat(series_list, axis=1)
    df.index.name = "Word"

    freq_cols = [s.name for s in series_list]
    spoken_cols = [c for c in _SPOKEN_COLS if c in df.columns]

    df["Agg Freq Avg"] = df[freq_cols].mean(axis=1, skipna=True)
    if spoken_cols:
        df["Agg Freq Min Spoken"] = df[spoken_cols].min(axis=1, skipna=True)
    else:
        df["Agg Freq Min Spoken"] = float("nan")
    df["Agg Freq Min"] = df[freq_cols].min(axis=1, skipna=True)

    return df
