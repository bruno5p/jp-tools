"""YouTube source and combined Anki pipelines."""

import json
import os
import re
from datetime import datetime

import pandas as pd

from .base import FullPipeline, Pipeline
from .models import AnkiCardData, YoutubeWordRow
from ..table_readers import TableReader

DEFAULT_ASR_MODEL = "kotoba-tech/kotoba-whisper-v2.2"
_PADDING = 0.25
_OUTPUT_COLS = list(AnkiCardData.model_fields.keys())


class PipelineYoutubeTranscribe(Pipeline):
    """Download, transcribe, and refine YouTube segments from a word table."""

    def __init__(
        self,
        table_reader: TableReader,
        output_csv: str = "output.csv",
        segments_dir: str = "segments",
        interval: float = 8,
        ytdlp: str | None = None,
        ffmpeg: str | None = None,
        model: str = DEFAULT_ASR_MODEL,
        device: str | None = None,
    ):
        self.table_reader = table_reader
        self.output_csv = output_csv
        self.segments_dir = segments_dir
        self.interval = interval
        self.model = model
        self.device = device
        self._ytdlp_hint = ytdlp
        self._ffmpeg_hint = ffmpeg
        self._downloader = None
        self._refiner = None
        self._transcriber = None

    # -- lazy tool accessors --------------------------------------------------

    def _ensure_downloader(self):
        if self._downloader is None:
            from ..video.segment_dl import SegmentDownloader

            self._downloader = SegmentDownloader(self._ytdlp_hint, self._ffmpeg_hint)
        return self._downloader

    def _ensure_refiner(self):
        if self._refiner is None:
            from ..video.refine_segment import SegmentRefiner

            self._refiner = SegmentRefiner(self._ffmpeg_hint)
        return self._refiner

    def _ensure_transcriber(self):
        if self._transcriber is None:
            from ..video.transcribe import Transcriber

            self._transcriber = Transcriber(self.model, self.device)
        return self._transcriber

    # -- pipeline steps -------------------------------------------------------

    def _download_segment(self, url: str, timestamp: str) -> str:
        from ..video.segment_dl import SegmentDownloader

        center = SegmentDownloader.parse_timestamp(timestamp)
        label = SegmentDownloader.format_label(center)
        os.makedirs(self.segments_dir, exist_ok=True)
        for f in os.listdir(self.segments_dir):
            if (
                re.match(rf"segment_\d+_{re.escape(label)}\.mp3$", f)
                and "_refined" not in f
            ):
                return os.path.join(self.segments_dir, f)
        self._ensure_downloader().download(
            url, [center], self.interval, self.segments_dir
        )
        for f in os.listdir(self.segments_dir):
            if (
                re.match(rf"segment_\d+_{re.escape(label)}\.mp3$", f)
                and "_refined" not in f
            ):
                return os.path.join(self.segments_dir, f)
        raise FileNotFoundError(f"segment not found after download for label '{label}'")

    def _transcribe(self, mp3_path: str) -> str:
        srt_path = os.path.splitext(mp3_path)[0] + ".srt"
        if not os.path.exists(srt_path):
            srt_content = self._ensure_transcriber().transcribe(mp3_path)
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content + "\n")
        return srt_path

    def _refine(self, mp3_path: str) -> str:
        return self._ensure_refiner().refine(mp3_path, padding=_PADDING)

    @staticmethod
    def _sentence_from_srt(srt_path: str, word: str) -> str:
        with open(srt_path, encoding="utf-8") as f:
            content = f.read()
        entries = []
        for block in re.split(r"\n\s*\n", content.strip()):
            lines = block.strip().splitlines()
            if len(lines) < 3:
                continue
            if not re.match(
                r"\d+:\d+:\d+[,\.]\d+\s*-->\s*\d+:\d+:\d+[,\.]\d+", lines[1].strip()
            ):
                continue
            text = " ".join(l.strip() for l in lines[2:] if l.strip())
            entries.append(text)
        for text in entries:
            if word in text:
                return text
        return max(entries, key=len) if entries else ""

    def _process_row(self, row: YoutubeWordRow) -> dict:
        source_meta = json.dumps({"video_url": row.video_url, "timestamp": row.timestamp})
        try:
            mp3_path = self._download_segment(row.video_url, row.timestamp)
            srt_path = self._transcribe(mp3_path)
            refined_path = self._refine(mp3_path)
            sentence = (
                self._sentence_from_srt(srt_path, row.word)
                if os.path.exists(srt_path)
                else ""
            )
            return AnkiCardData(
                added_on=datetime.now(),
                word=row.word,
                hint=row.hint or None,
                sentence=sentence or None,
                sentence_audio_path=os.path.abspath(refined_path)
                if os.path.exists(refined_path)
                else None,
                source_metadata=source_meta,
                status="ok",
            ).to_csv_row()
        except Exception as e:
            return AnkiCardData(
                added_on=datetime.now(),
                word=row.word,
                hint=row.hint or None,
                source_metadata=source_meta,
                status="error",
                status_message=str(e),
            ).to_csv_row()

    # -- public interface -----------------------------------------------------

    def run(self) -> str:
        rows = YoutubeWordRow.from_df(self.table_reader.read())
        done: set[tuple[str, str]] = set()
        results: list[dict] = []

        if os.path.exists(self.output_csv):
            existing = pd.read_csv(self.output_csv).fillna("")
            ok_rows = (
                existing[existing["status"] == "ok"]
                if "status" in existing.columns
                else existing
            )
            for _, r in ok_rows.iterrows():
                try:
                    meta = json.loads(r.get("source_metadata", "") or "")
                except (json.JSONDecodeError, ValueError):
                    meta = {}
                done.add(
                    (
                        meta.get("video_url", "").strip(),
                        meta.get("timestamp", "").strip(),
                    )
                )
                results.append({col: r.get(col, "") for col in _OUTPUT_COLS})

        for row in rows:
            key = (row.video_url, row.timestamp)
            if key in done:
                print(f"  [skip] {row.word} @ {row.timestamp}")
                continue
            print(f"\n→ {row.word}  @  {row.timestamp}")
            results.append(self._process_row(row))

        out_df = pd.DataFrame(results, columns=_OUTPUT_COLS)
        out_df.to_csv(self.output_csv, index=False)
        errors = out_df[out_df["status"] == "error"]
        print(f"\nDone. {len(out_df)} row(s) written to: {self.output_csv}")
        if not errors.empty:
            print(f"Failed rows ({len(errors)}): {errors['word'].tolist()}")
        return self.output_csv

    def reprocess_errors(self) -> str:
        """Reprocess rows with status='error' in the output CSV and save in-place."""
        existing = pd.read_csv(self.output_csv).fillna("")
        if "status" not in existing.columns:
            print("No 'status' column found — nothing to reprocess.")
            return self.output_csv
        error_mask = existing["status"] == "error"
        if not error_mask.any():
            print("No error rows to reprocess.")
            return self.output_csv
        for idx, row in existing[error_mask].iterrows():
            try:
                meta = json.loads(row.get("source_metadata", "") or "")
            except (json.JSONDecodeError, ValueError):
                meta = {}
            word_row = YoutubeWordRow(
                video_url=meta.get("video_url", ""),
                word=str(row.get("word", "")),
                timestamp=meta.get("timestamp", ""),
                hint=str(row.get("hint", "") or ""),
            )
            result = self._process_row(word_row)
            for col, val in result.items():
                if col in existing.columns:
                    existing.at[idx, col] = val
        existing.to_csv(self.output_csv, index=False)
        print(f"Reprocessed {int(error_mask.sum())} error row(s).")
        return self.output_csv


class PipelineYoutubeToAnki(FullPipeline):
    """Build an Anki deck directly from a YouTube word table.

    Chains :class:`PipelineYoutubeTranscribe` → :class:`PipelineAnkiFromList`,
    with optional filter, all-cards accumulation, and WordDex update steps
    inherited from :class:`FullPipeline`.
    """

    def __init__(
        self,
        table_reader: TableReader,
        output: str = "deck.apkg",
        deck_name: str = "Japanese Mining",
        output_csv: str = "output.csv",
        segments_dir: str = "segments",
        interval: float = 8,
        ytdlp: str | None = None,
        ffmpeg: str | None = None,
        model: str = DEFAULT_ASR_MODEL,
        device: str | None = None,
        dicts_dir: str | None = None,
        dict_names: list[str] | None = None,
        pitch_name: str | None = None,
        freq_names: list[str] | None = None,
        word_audio: bool = True,
        audio_timeout: float = 10,
        worddex_csv: str | None = None,
        all_cards_csv: str | None = None,
        filter_known: bool = True,
        append_all_cards: bool = True,
        update_worddex: bool = True,
    ):
        super().__init__(
            worddex_csv=worddex_csv,
            all_cards_csv=all_cards_csv,
            filter_known=filter_known,
            append_all_cards=append_all_cards,
            update_worddex=update_worddex,
        )
        self.transcribe = PipelineYoutubeTranscribe(
            table_reader,
            output_csv=output_csv,
            segments_dir=segments_dir,
            interval=interval,
            ytdlp=ytdlp,
            ffmpeg=ffmpeg,
            model=model,
            device=device,
        )
        self.output = output
        self.deck_name = deck_name
        self.dicts_dir = dicts_dir
        self.dict_names = dict_names
        self.pitch_name = pitch_name
        self.freq_names = freq_names
        self.word_audio = word_audio
        self.audio_timeout = audio_timeout

    def _source_run(self) -> str:
        return self.transcribe.run()

    def _sink_run(self, csv_path: str) -> str:
        from .pipeline_anki import PipelineAnkiFromList

        return PipelineAnkiFromList(
            csv_path,
            output=self.output,
            deck_name=self.deck_name,
            dicts_dir=self.dicts_dir,
            dict_names=self.dict_names,
            pitch_name=self.pitch_name,
            freq_names=self.freq_names,
            word_audio=self.word_audio,
            audio_timeout=self.audio_timeout,
        ).run()
