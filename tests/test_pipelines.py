"""Integration tests for YoutubeTranscribePipeline."""

from pathlib import Path

import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"

_SRT = {
    "13m38s": "1\n00:00:00,000 --> 00:00:05,000\nああ忘れ物しちゃったな\n",
    "5m40s":  "1\n00:00:00,000 --> 00:00:05,000\nカジュアルな話カジュアルトークフリートーク雑談ですね\n",
}
_LABEL_BY_TS = {"13:38": "13m38s", "5:40": "5m40s"}


def _make_segments(segments_dir: Path) -> dict[str, str]:
    """Create stub mp3 / srt / refined-mp3 files; return label → mp3 path."""
    paths = {}
    for label, srt_text in _SRT.items():
        mp3 = segments_dir / f"segment_001_{label}.mp3"
        srt = segments_dir / f"segment_001_{label}.srt"
        refined = segments_dir / f"segment_001_{label}_refined.mp3"
        mp3.touch()
        refined.touch()
        srt.write_text(srt_text, encoding="utf-8")
        paths[label] = str(mp3)
    return paths


def _make_pipeline(tmp_path, output_csv=None):
    from jp_tools.pipelines.youtube_transcribe import YoutubeTranscribePipeline
    segments_dir = tmp_path / "segments"
    segments_dir.mkdir()
    return YoutubeTranscribePipeline(
        input_table=str(FIXTURES / "words.csv"),
        output_csv=str(output_csv or tmp_path / "output.csv"),
        segments_dir=str(segments_dir),
    ), segments_dir


class TestYoutubeTranscribePipeline:
    def test_run_ok(self, tmp_path):
        pipeline, segments_dir = _make_pipeline(tmp_path)
        seg_paths = _make_segments(segments_dir)

        def fake_download(url, timestamp):
            return seg_paths[_LABEL_BY_TS[timestamp.strip()]]

        pipeline._download_segment = fake_download
        pipeline._transcribe = lambda p: p.replace(".mp3", ".srt")
        pipeline._refine = lambda p: p.replace(".mp3", "_refined.mp3")

        pipeline.run()

        df = pd.read_csv(pipeline.output_csv)
        assert list(df.columns) == ["video_url", "timestamp", "word", "sentence", "ref_audio_path", "status", "status_message"]
        assert len(df) == 2
        assert (df["status"] == "ok").all()
        assert df.loc[df["word"] == "忘れ物", "sentence"].iloc[0] == "ああ忘れ物しちゃったな"
        assert df.loc[df["word"] == "雑談", "sentence"].iloc[0] == "カジュアルな話カジュアルトークフリートーク雑談ですね"
        assert df["ref_audio_path"].str.endswith("_refined.mp3").all()

    def test_error_row_captured(self, tmp_path):
        pipeline, _ = _make_pipeline(tmp_path)

        def fail(url, timestamp):
            raise RuntimeError("yt-dlp failed")

        pipeline._download_segment = fail
        pipeline.run()

        df = pd.read_csv(pipeline.output_csv)
        assert (df["status"] == "error").all()
        assert df["status_message"].str.contains("yt-dlp failed").all()

    def test_skips_ok_rows(self, tmp_path):
        output_csv = tmp_path / "output.csv"
        pipeline, segments_dir = _make_pipeline(tmp_path, output_csv)
        seg_paths = _make_segments(segments_dir)

        pd.DataFrame([{
            "video_url": "https://www.youtube.com/watch?v=67-fAdvRpSA",
            "timestamp": "13:38",
            "word": "忘れ物",
            "sentence": "ああ忘れ物しちゃったな",
            "ref_audio_path": "/fake/refined.mp3",
            "status": "ok",
            "status_message": "",
        }]).to_csv(output_csv, index=False)

        download_calls: list[str] = []

        def fake_download(url, timestamp):
            download_calls.append(timestamp.strip())
            return seg_paths[_LABEL_BY_TS[timestamp.strip()]]

        pipeline._download_segment = fake_download
        pipeline._transcribe = lambda p: p.replace(".mp3", ".srt")
        pipeline._refine = lambda p: p.replace(".mp3", "_refined.mp3")
        pipeline.run()

        assert download_calls == ["5:40"]

    def test_reprocess_errors(self, tmp_path):
        output_csv = tmp_path / "output.csv"
        pipeline, segments_dir = _make_pipeline(tmp_path, output_csv)
        seg_paths = _make_segments(segments_dir)

        pd.DataFrame([
            {
                "video_url": "https://www.youtube.com/watch?v=67-fAdvRpSA",
                "timestamp": "13:38", "word": "忘れ物",
                "sentence": "ああ忘れ物しちゃったな", "ref_audio_path": "/fake/refined.mp3",
                "status": "ok", "status_message": "",
            },
            {
                "video_url": "https://www.youtube.com/watch?v=xI8EDxU4Q6g",
                "timestamp": "5:40", "word": "雑談",
                "sentence": "", "ref_audio_path": "",
                "status": "error", "status_message": "network error",
            },
        ]).to_csv(output_csv, index=False)

        def fake_download(url, timestamp):
            return seg_paths[_LABEL_BY_TS[timestamp.strip()]]

        pipeline._download_segment = fake_download
        pipeline._transcribe = lambda p: p.replace(".mp3", ".srt")
        pipeline._refine = lambda p: p.replace(".mp3", "_refined.mp3")
        pipeline.reprocess_errors()

        df = pd.read_csv(output_csv)
        assert len(df) == 2
        assert (df["status"] == "ok").all()
        assert df.loc[df["word"] == "雑談", "sentence"].iloc[0] == "カジュアルな話カジュアルトークフリートーク雑談ですね"
