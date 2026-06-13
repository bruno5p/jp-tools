"""Integration tests for YoutubeTranscribePipeline."""

import csv
import sqlite3
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
INTEGRATION_DATA = Path(__file__).parent / "integration_data"

_SRT = {
    "13m38s": "1\n00:00:00,000 --> 00:00:05,000\nああ忘れ物しちゃったな\n",
    "5m40s": "1\n00:00:00,000 --> 00:00:05,000\nカジュアルな話カジュアルトークフリートーク雑談ですね\n",
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


# class TestYoutubeTranscribePipeline:
#     def test_run_ok(self, tmp_path):
#         pipeline, segments_dir = _make_pipeline(tmp_path)
#         seg_paths = _make_segments(segments_dir)

#         def fake_download(url, timestamp):
#             return seg_paths[_LABEL_BY_TS[timestamp.strip()]]

#         pipeline._download_segment = fake_download
#         pipeline._transcribe = lambda p: p.replace(".mp3", ".srt")
#         pipeline._refine = lambda p: p.replace(".mp3", "_refined.mp3")

#         pipeline.run()

#         df = pd.read_csv(pipeline.output_csv)
#         assert list(df.columns) == ["video_url", "timestamp", "word", "sentence", "ref_audio_path", "status", "status_message"]
#         assert len(df) == 2
#         assert (df["status"] == "ok").all()
#         assert df.loc[df["word"] == "忘れ物", "sentence"].iloc[0] == "ああ忘れ物しちゃったな"
#         assert df.loc[df["word"] == "雑談", "sentence"].iloc[0] == "カジュアルな話カジュアルトークフリートーク雑談ですね"
#         assert df["ref_audio_path"].str.endswith("_refined.mp3").all()

#     def test_error_row_captured(self, tmp_path):
#         pipeline, _ = _make_pipeline(tmp_path)

#         def fail(url, timestamp):
#             raise RuntimeError("yt-dlp failed")

#         pipeline._download_segment = fail
#         pipeline.run()

#         df = pd.read_csv(pipeline.output_csv)
#         assert (df["status"] == "error").all()
#         assert df["status_message"].str.contains("yt-dlp failed").all()

#     def test_skips_ok_rows(self, tmp_path):
#         output_csv = tmp_path / "output.csv"
#         pipeline, segments_dir = _make_pipeline(tmp_path, output_csv)
#         seg_paths = _make_segments(segments_dir)

#         pd.DataFrame([{
#             "video_url": "https://www.youtube.com/watch?v=67-fAdvRpSA",
#             "timestamp": "13:38",
#             "word": "忘れ物",
#             "sentence": "ああ忘れ物しちゃったな",
#             "ref_audio_path": "/fake/refined.mp3",
#             "status": "ok",
#             "status_message": "",
#         }]).to_csv(output_csv, index=False)

#         download_calls: list[str] = []

#         def fake_download(url, timestamp):
#             download_calls.append(timestamp.strip())
#             return seg_paths[_LABEL_BY_TS[timestamp.strip()]]

#         pipeline._download_segment = fake_download
#         pipeline._transcribe = lambda p: p.replace(".mp3", ".srt")
#         pipeline._refine = lambda p: p.replace(".mp3", "_refined.mp3")
#         pipeline.run()

#         assert download_calls == ["5:40"]

#     def test_reprocess_errors(self, tmp_path):
#         output_csv = tmp_path / "output.csv"
#         pipeline, segments_dir = _make_pipeline(tmp_path, output_csv)
#         seg_paths = _make_segments(segments_dir)

#         pd.DataFrame([
#             {
#                 "video_url": "https://www.youtube.com/watch?v=67-fAdvRpSA",
#                 "timestamp": "13:38", "word": "忘れ物",
#                 "sentence": "ああ忘れ物しちゃったな", "ref_audio_path": "/fake/refined.mp3",
#                 "status": "ok", "status_message": "",
#             },
#             {
#                 "video_url": "https://www.youtube.com/watch?v=xI8EDxU4Q6g",
#                 "timestamp": "5:40", "word": "雑談",
#                 "sentence": "", "ref_audio_path": "",
#                 "status": "error", "status_message": "network error",
#             },
#         ]).to_csv(output_csv, index=False)

#         def fake_download(url, timestamp):
#             return seg_paths[_LABEL_BY_TS[timestamp.strip()]]

#         pipeline._download_segment = fake_download
#         pipeline._transcribe = lambda p: p.replace(".mp3", ".srt")
#         pipeline._refine = lambda p: p.replace(".mp3", "_refined.mp3")
#         pipeline.reprocess_errors()

#         df = pd.read_csv(output_csv)
#         assert len(df) == 2
#         assert (df["status"] == "ok").all()
#         assert df.loc[df["word"] == "雑談", "sentence"].iloc[0] == "カジュアルな話カジュアルトークフリートーク雑談ですね"


def _apkg_note_count(apkg_path: Path, tmp_path: Path) -> int:
    """Extract collection.anki2 from an .apkg and return the number of notes."""
    with zipfile.ZipFile(apkg_path) as zf:
        db_bytes = zf.read("collection.anki2")
    db_path = tmp_path / "collection.anki2"
    db_path.write_bytes(db_bytes)
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    finally:
        conn.close()


class TestListCreateAnkiPipeline:
    def test_run_creates_apkg_with_correct_card_count(self, tmp_path):
        from jp_tools.lookup import DictResult
        from jp_tools.pipelines.list_create_anki import ListCreateAnkiPipeline

        fixture_csv = FIXTURES / "anki_words_list.csv"
        with open(fixture_csv, encoding="utf-8") as f:
            expected_cards = sum(
                1 for row in csv.DictReader(f) if row.get("word", "").strip()
            )

        # Empty dict folder so os.path.isdir passes the dict check
        fake_jmdict = tmp_path / "jmdict"
        fake_jmdict.mkdir()

        stub_result = DictResult(
            expression="stub",
            reading="よみ",
            definitions=["stub definition"],
            pos=[],
            pitch_position=1,
            pitch_category="atamadaka",
            frequencies=[("JPDB", 100)],
        )
        mock_dict_set = MagicMock()
        mock_dict_set.find_term.return_value = stub_result

        INTEGRATION_DATA.mkdir(exist_ok=True)
        output_apkg = INTEGRATION_DATA / "deck.apkg"

        try:
            with (
                patch("jp_tools.lookup.get_dict", return_value=mock_dict_set),
                patch(
                    "jp_tools.furigana.get_furigana_plain",
                    side_effect=lambda w, r: w,
                ),
                patch(
                    "jp_tools.furigana.get_sentence_furigana",
                    side_effect=lambda s: s,
                ),
            ):
                pipeline = ListCreateAnkiPipeline(
                    csv_path=str(fixture_csv),
                    output=str(output_apkg),
                    jmdict=str(fake_jmdict),
                    word_audio=False,  # keep the test offline / network-free
                )
                result = pipeline.run()

            assert output_apkg.exists(), f".apkg not created at {output_apkg}"
            assert result == str(output_apkg)
            assert _apkg_note_count(output_apkg, tmp_path) == expected_cards
        finally:
            output_apkg.unlink(missing_ok=True)
