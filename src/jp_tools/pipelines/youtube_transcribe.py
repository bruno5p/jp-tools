import os
import re

import pandas as pd

from .base import Pipeline

DEFAULT_ASR_MODEL = "kotoba-tech/kotoba-whisper-v2.2"
_PADDING = 0.25
_OUTPUT_COLS = ["video_url", "timestamp", "word", "sentence", "ref_audio_path", "status", "status_message"]


class YoutubeTranscribePipeline(Pipeline):
    """Download, transcribe, and refine YouTube segments from a word table."""

    def __init__(
        self,
        input_table: str,
        output_csv: str = "output.csv",
        segments_dir: str = "segments",
        interval: float = 8,
        ytdlp: str | None = None,
        ffmpeg: str | None = None,
        model: str = DEFAULT_ASR_MODEL,
        device: str | None = None,
    ):
        self.input_table = input_table
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
            if re.match(rf"segment_\d+_{re.escape(label)}\.mp3$", f) and "_refined" not in f:
                return os.path.join(self.segments_dir, f)
        self._ensure_downloader().download(url, [center], self.interval, self.segments_dir)
        for f in os.listdir(self.segments_dir):
            if re.match(rf"segment_\d+_{re.escape(label)}\.mp3$", f) and "_refined" not in f:
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
            if not re.match(r"\d+:\d+:\d+[,\.]\d+\s*-->\s*\d+:\d+:\d+[,\.]\d+", lines[1].strip()):
                continue
            text = " ".join(l.strip() for l in lines[2:] if l.strip())
            entries.append(text)
        for text in entries:
            if word in text:
                return text
        return max(entries, key=len) if entries else ""

    def _process_row(self, row) -> dict:
        url = str(row["video_url"]).strip()
        timestamp = str(row["timestamp"]).strip()
        word = str(row["word"]).strip()
        result = {
            "video_url": url, "timestamp": timestamp, "word": word,
            "sentence": "", "ref_audio_path": "",
            "status": "error", "status_message": "",
        }
        try:
            mp3_path = self._download_segment(url, timestamp)
            srt_path = self._transcribe(mp3_path)
            refined_path = self._refine(mp3_path)
            sentence = self._sentence_from_srt(srt_path, word) if os.path.exists(srt_path) else ""
            result.update({
                "sentence": sentence,
                "ref_audio_path": os.path.abspath(refined_path) if os.path.exists(refined_path) else "",
                "status": "ok",
                "status_message": "",
            })
        except Exception as e:
            result["status_message"] = str(e)
        return result

    # -- public interface -----------------------------------------------------

    def run(self) -> str:
        df = pd.read_csv(self.input_table)
        done: set[tuple[str, str]] = set()
        results: list[dict] = []

        if os.path.exists(self.output_csv):
            existing = pd.read_csv(self.output_csv)
            ok_rows = existing[existing["status"] == "ok"] if "status" in existing.columns else existing
            for _, r in ok_rows.iterrows():
                done.add((str(r["video_url"]).strip(), str(r["timestamp"]).strip()))
                results.append({col: r.get(col, "") for col in _OUTPUT_COLS})

        for _, row in df.iterrows():
            key = (str(row["video_url"]).strip(), str(row["timestamp"]).strip())
            if key in done:
                print(f"  [skip] {row.get('word', '')} @ {row['timestamp']}")
                continue
            print(f"\n→ {row.get('word', '')}  @  {row['timestamp']}")
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
        existing = pd.read_csv(self.output_csv)
        if "status" not in existing.columns:
            print("No 'status' column found — nothing to reprocess.")
            return self.output_csv
        error_mask = existing["status"] == "error"
        if not error_mask.any():
            print("No error rows to reprocess.")
            return self.output_csv
        for idx, row in existing[error_mask].iterrows():
            result = self._process_row(row)
            for col, val in result.items():
                if col in existing.columns:
                    existing.at[idx, col] = val
        existing.to_csv(self.output_csv, index=False)
        print(f"Reprocessed {int(error_mask.sum())} error row(s).")
        return self.output_csv
