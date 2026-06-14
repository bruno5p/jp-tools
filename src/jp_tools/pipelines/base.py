"""Base classes for composable jp_tools pipelines."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd


class Pipeline(ABC):
    """A pipeline bundles a sequence of building-block steps behind one entry point.

    Subclasses take their configuration in ``__init__`` (paths, options) and do
    the work in :meth:`run`, composing functions from :mod:`jp_tools.core` and/or
    other pipelines. ``run`` should return its primary output (e.g. the path of a
    produced file) so pipelines can be chained.
    """

    @abstractmethod
    def run(self) -> Any:
        """Execute the pipeline and return its primary output."""
        raise NotImplementedError


class FullPipeline(Pipeline):
    """Pipeline with filter → source → sink → post-processing hooks.

    Subclasses implement :meth:`_source_run` (produces an AnkiCardData CSV) and
    :meth:`_sink_run` (consumes the CSV and produces an .apkg). :meth:`run`
    orchestrates the three optional cross-cutting concerns:

    - **filter_known**: skip words where ``Anki (word)==1`` in the WordDex CSV.
    - **append_all_cards**: append newly created cards to a master CSV so the
      full deck can be rebuilt anytime with ``PipelineAnkiFromList``.
    - **update_worddex**: set ``Anki (word)=1`` / ``Anki (sentence)=1`` for
      successfully created cards.

    All three are enabled by default. A ``ValueError`` is raised at construction
    time if a feature is enabled but its required path is not supplied.
    """

    def __init__(
        self,
        worddex_csv: str | None = None,
        all_cards_csv: str | None = None,
        filter_known: bool = True,
        append_all_cards: bool = True,
        update_worddex: bool = True,
    ):
        if filter_known and worddex_csv is None:
            raise ValueError("worddex_csv is required when filter_known=True")
        if update_worddex and worddex_csv is None:
            raise ValueError("worddex_csv is required when update_worddex=True")
        if append_all_cards and all_cards_csv is None:
            raise ValueError("all_cards_csv is required when append_all_cards=True")
        self.worddex_csv = worddex_csv
        self.all_cards_csv = all_cards_csv
        self.filter_known = filter_known
        self.append_all_cards = append_all_cards
        self.update_worddex = update_worddex

    @abstractmethod
    def _source_run(self) -> str:
        """Run the source step and return the path to an AnkiCardData CSV."""
        raise NotImplementedError

    @abstractmethod
    def _sink_run(self, csv_path: str) -> str:
        """Build the .apkg from *csv_path* and return the .apkg path."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Hook implementations
    # ------------------------------------------------------------------

    def _filter_csv(self, source_csv: str) -> str:
        """Mark already-known words as status='skip' and write a new CSV."""
        wdx = pd.read_csv(self.worddex_csv, index_col=0)
        known: set[str] = set(wdx[wdx["Anki (word)"] == 1].index.astype(str))

        df = pd.read_csv(source_csv, dtype=str).fillna("")
        mask = df["word"].isin(known)
        df.loc[mask, "status"] = "skip"
        df.loc[mask, "status_message"] = "already in Anki"

        stem = Path(source_csv).stem
        out_path = os.path.join(os.path.dirname(source_csv), f"{stem}_filtered.csv")
        df.to_csv(out_path, index=False)

        skipped = int(mask.sum())
        if skipped:
            print(f"[filter] {skipped} word(s) skipped (already in Anki)")
        return out_path

    def _do_append_all_cards(self, card_csv: str) -> None:
        """Append status='ok' rows from *card_csv* to the master all-cards CSV."""
        new_df = pd.read_csv(card_csv, dtype=str).fillna("")
        new_ok = new_df[new_df["status"] == "ok"]
        if new_ok.empty:
            return

        if os.path.exists(self.all_cards_csv):
            existing = pd.read_csv(self.all_cards_csv, dtype=str).fillna("")
            combined = pd.concat([existing, new_ok], ignore_index=True)
            combined = combined.drop_duplicates(subset=["word"], keep="last")
        else:
            combined = new_ok

        combined.to_csv(self.all_cards_csv, index=False, encoding="utf-8-sig")
        print(f"[all-cards] {len(new_ok)} row(s) appended → {self.all_cards_csv}")

    def _do_update_worddex(self, card_csv: str) -> None:
        """Set Anki (word)=1 and Anki (sentence)=1 for newly created cards."""
        new_df = pd.read_csv(card_csv, dtype=str).fillna("")
        new_words: set[str] = set(new_df.loc[new_df["status"] == "ok", "word"])
        if not new_words:
            return

        wdx = pd.read_csv(self.worddex_csv, index_col=0)
        hits = wdx.index.isin(new_words)
        wdx.loc[hits, "Anki (word)"] = 1
        wdx.loc[hits, "Anki (sentence)"] = 1
        if "Learned" in wdx.columns:
            wdx["Learned"] = (
                (wdx["Anki (word)"] + wdx["Anki (sentence)"]) > 0
            ).astype(int)
        wdx.to_csv(self.worddex_csv, encoding="utf-8-sig")
        print(f"[worddex] {int(hits.sum())} word(s) updated → {self.worddex_csv}")

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run(self) -> str:
        source_csv = self._source_run()
        card_csv = self._filter_csv(source_csv) if self.filter_known else source_csv
        apkg_path = self._sink_run(card_csv)
        if self.append_all_cards:
            self._do_append_all_cards(card_csv)
        if self.update_worddex:
            self._do_update_worddex(card_csv)
        return apkg_path
