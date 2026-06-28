"""Tests for PipelineAnkiFromList, FullPipeline hooks, and PipelineYoutubeToAnki."""

import csv
import sqlite3
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from jp_tools.pipelines.base import FullPipeline

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
    from jp_tools.pipelines.pipeline_youtube import PipelineYoutubeTranscribe

    segments_dir = tmp_path / "segments"
    segments_dir.mkdir()
    return PipelineYoutubeTranscribe(
        input_table=str(FIXTURES / "words.csv"),
        output_csv=str(output_csv or tmp_path / "output.csv"),
        segments_dir=str(segments_dir),
    ), segments_dir


# class TestPipelineYoutubeTranscribe:
#     def test_run_ok(self, tmp_path):
#         pipeline, segments_dir = _make_pipeline(tmp_path)
#         seg_paths = _make_segments(segments_dir)

#         def fake_download(url, timestamp):
#             return seg_paths[_LABEL_BY_TS[timestamp.strip()]]

#         pipeline._download_segment = fake_download
#         pipeline._transcribe = lambda p: p.replace(".mp3", ".srt")
#         pipeline._refine = lambda p: p.replace(".mp3", "_refined.mp3")

#         pipeline.run()

#         from jp_tools.pipelines.models import AnkiCardData
#         df = pd.read_csv(pipeline.output_csv)
#         assert list(df.columns) == list(AnkiCardData.model_fields.keys())
#         assert len(df) == 2
#         assert (df["status"] == "ok").all()
#         assert df.loc[df["word"] == "忘れ物", "sentence"].iloc[0] == "ああ忘れ物しちゃったな"
#         assert df.loc[df["word"] == "雑談", "sentence"].iloc[0] == "カジュアルな話カジュアルトークフリートーク雑談ですね"
#         assert df["sentence_audio_path"].str.endswith("_refined.mp3").all()

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
#         from datetime import datetime
#         output_csv = tmp_path / "output.csv"
#         pipeline, segments_dir = _make_pipeline(tmp_path, output_csv)
#         seg_paths = _make_segments(segments_dir)

#         pd.DataFrame([{
#             "added_on": datetime.now().isoformat(),
#             "word": "忘れ物",
#             "sentence": "ああ忘れ物しちゃったな",
#             "sentence_audio_path": "/fake/refined.mp3",
#             "source_metadata": '{"video_url": "https://www.youtube.com/watch?v=67-fAdvRpSA", "timestamp": "13:38"}',
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
#         from datetime import datetime
#         output_csv = tmp_path / "output.csv"
#         pipeline, segments_dir = _make_pipeline(tmp_path, output_csv)
#         seg_paths = _make_segments(segments_dir)

#         pd.DataFrame([
#             {
#                 "added_on": datetime.now().isoformat(),
#                 "word": "忘れ物",
#                 "sentence": "ああ忘れ物しちゃったな",
#                 "sentence_audio_path": "/fake/refined.mp3",
#                 "source_metadata": '{"video_url": "https://www.youtube.com/watch?v=67-fAdvRpSA", "timestamp": "13:38"}',
#                 "status": "ok",
#                 "status_message": "",
#             },
#             {
#                 "added_on": datetime.now().isoformat(),
#                 "word": "雑談",
#                 "sentence": "",
#                 "sentence_audio_path": "",
#                 "source_metadata": '{"video_url": "https://www.youtube.com/watch?v=xI8EDxU4Q6g", "timestamp": "5:40"}',
#                 "status": "error",
#                 "status_message": "network error",
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


# ---- shared CSV helpers ----------------------------------------------------

_CARD_FIELDS = [
    "added_on", "word", "reading", "sentence", "word_audio_path",
    "sentence_audio_path", "picture_path", "definition",
    "definition_picture_path", "hint", "tags", "source_metadata",
    "status", "status_message",
]


def _card_row(**overrides):
    base = {f: "" for f in _CARD_FIELDS}
    base["added_on"] = "2026-01-01T00:00:00"
    base["status"] = "ok"
    base.update(overrides)
    return base


def _write_card_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_CARD_FIELDS)
        w.writeheader()
        w.writerows(rows)


def _write_worddex(path, entries):
    """entries: {word: anki_word_flag} — flag 0 or 1 sets Anki (word)."""
    df = pd.DataFrame(
        {
            "Learned": {w: flag for w, flag in entries.items()},
            "Anki (word)": {w: flag for w, flag in entries.items()},
            "Anki (sentence)": {w: 0 for w in entries},
        }
    )
    df.index.name = "Word"
    df.to_csv(path, encoding="utf-8-sig")


# ---- FullPipeline test double ----------------------------------------------

class _FakePipeline(FullPipeline):
    """Minimal FullPipeline subclass for testing hooks in isolation."""

    def __init__(self, src_csv, **kw):
        super().__init__(**kw)
        self._src = src_csv

    def _source_run(self):
        return self._src

    def _sink_run(self, csv_path):
        return "fake.apkg"


# ---------------------------------------------------------------------------

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


class TestPipelineAnkiFromList:
    def test_run_creates_apkg_with_correct_card_count(self, tmp_path):
        from jp_tools.lookup import DictResult
        from jp_tools.pipelines.pipeline_anki import PipelineAnkiFromList

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
        mock_dict_set.find_all_terms.return_value = [stub_result]

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
                pipeline = PipelineAnkiFromList(
                    csv_path=str(fixture_csv),
                    output=str(output_apkg),
                    dicts_dir=str(tmp_path),
                    dict_names=["jmdict"],
                    word_audio=False,  # keep the test offline / network-free
                )
                result = pipeline.run()

            assert output_apkg.exists(), f".apkg not created at {output_apkg}"
            assert result == str(output_apkg)
            assert _apkg_note_count(output_apkg, tmp_path) == expected_cards
        finally:
            output_apkg.unlink(missing_ok=True)

    def test_skip_rows_are_not_created(self, tmp_path):
        """status='skip' rows must not produce Anki cards."""
        from jp_tools.pipelines.pipeline_anki import PipelineAnkiFromList

        csv_path = tmp_path / "words.csv"
        _write_card_csv(csv_path, [
            _card_row(word="taberu", status="ok"),
            _card_row(word="suru", status="skip", status_message="already in Anki"),
        ])

        with patch("jp_tools.anki.creator.AnkiCardCreator") as MockCreator:
            mock_instance = MockCreator.return_value
            mock_instance.add_word.return_value = "added"
            PipelineAnkiFromList(str(csv_path), output=str(tmp_path / "deck.apkg"), word_audio=False).run()

        assert mock_instance.add_word.call_count == 1
        assert mock_instance.add_word.call_args.kwargs["word"] == "taberu"


class TestFullPipeline:
    # -- construction validation --------------------------------------------

    def test_init_raises_for_filter_without_worddex(self):
        with pytest.raises(ValueError, match="worddex_csv"):
            _FakePipeline("x.csv", filter_known=True, append_all_cards=False, update_worddex=False)

    def test_init_raises_for_update_without_worddex(self):
        with pytest.raises(ValueError, match="worddex_csv"):
            _FakePipeline("x.csv", filter_known=False, append_all_cards=False, update_worddex=True)

    def test_init_raises_for_append_without_all_cards_csv(self):
        with pytest.raises(ValueError, match="all_cards_csv"):
            _FakePipeline("x.csv", filter_known=False, append_all_cards=True, update_worddex=False)

    def test_init_all_disabled_requires_no_paths(self):
        p = _FakePipeline("x.csv", filter_known=False, append_all_cards=False, update_worddex=False)
        assert isinstance(p, FullPipeline)

    # -- _filter_csv --------------------------------------------------------

    def test_filter_csv_marks_known_words_as_skip(self, tmp_path):
        worddex = tmp_path / "worddex.csv"
        src = tmp_path / "output.csv"
        _write_worddex(worddex, {"suru": 1, "taberu": 0})
        _write_card_csv(src, [
            _card_row(word="suru"),
            _card_row(word="taberu"),
            _card_row(word="hashiru"),  # not in worddex at all
        ])

        p = _FakePipeline(str(src), worddex_csv=str(worddex), filter_known=True, append_all_cards=False, update_worddex=False)
        filtered = p._filter_csv(str(src))
        df = pd.read_csv(filtered)

        assert df.loc[df["word"] == "suru", "status"].iloc[0] == "skip"
        assert df.loc[df["word"] == "taberu", "status"].iloc[0] == "ok"
        assert df.loc[df["word"] == "hashiru", "status"].iloc[0] == "ok"

    def test_filter_csv_leaves_original_unchanged(self, tmp_path):
        worddex = tmp_path / "worddex.csv"
        src = tmp_path / "output.csv"
        _write_worddex(worddex, {"suru": 1})
        _write_card_csv(src, [_card_row(word="suru")])
        original = src.read_text(encoding="utf-8")

        p = _FakePipeline(str(src), worddex_csv=str(worddex), filter_known=True, append_all_cards=False, update_worddex=False)
        p._filter_csv(str(src))

        assert src.read_text(encoding="utf-8") == original

    def test_filter_csv_returns_filtered_path(self, tmp_path):
        worddex = tmp_path / "worddex.csv"
        src = tmp_path / "output.csv"
        _write_worddex(worddex, {})
        _write_card_csv(src, [_card_row(word="suru")])

        p = _FakePipeline(str(src), worddex_csv=str(worddex), filter_known=True, append_all_cards=False, update_worddex=False)
        filtered = p._filter_csv(str(src))

        assert filtered == str(tmp_path / "output_filtered.csv")

    # -- _do_append_all_cards -----------------------------------------------

    def test_append_all_cards_only_includes_ok_rows(self, tmp_path):
        src = tmp_path / "cards.csv"
        all_cards = tmp_path / "all.csv"
        _write_card_csv(src, [
            _card_row(word="taberu", status="ok"),
            _card_row(word="suru", status="error"),
            _card_row(word="hashiru", status="skip"),
        ])

        p = _FakePipeline(str(src), filter_known=False, append_all_cards=True, update_worddex=False, all_cards_csv=str(all_cards))
        p._do_append_all_cards(str(src))

        df = pd.read_csv(all_cards)
        assert list(df["word"]) == ["taberu"]

    def test_append_all_cards_deduplicates_on_second_run(self, tmp_path):
        src = tmp_path / "cards.csv"
        all_cards = tmp_path / "all.csv"
        _write_card_csv(src, [_card_row(word="taberu")])

        p = _FakePipeline(str(src), filter_known=False, append_all_cards=True, update_worddex=False, all_cards_csv=str(all_cards))
        p._do_append_all_cards(str(src))
        p._do_append_all_cards(str(src))

        df = pd.read_csv(all_cards)
        assert len(df) == 1

    # -- _do_update_worddex -------------------------------------------------

    def test_update_worddex_sets_anki_flags_for_ok_rows(self, tmp_path):
        worddex = tmp_path / "worddex.csv"
        src = tmp_path / "cards.csv"
        _write_worddex(worddex, {"taberu": 0, "suru": 0})
        _write_card_csv(src, [
            _card_row(word="taberu", status="ok"),
            _card_row(word="suru", status="error"),
        ])

        p = _FakePipeline(str(src), worddex_csv=str(worddex), filter_known=False, append_all_cards=False, update_worddex=True)
        p._do_update_worddex(str(src))

        wdx = pd.read_csv(worddex, index_col=0)
        assert wdx.loc["taberu", "Anki (word)"] == 1
        assert wdx.loc["taberu", "Anki (sentence)"] == 1
        assert wdx.loc["suru", "Anki (word)"] == 0   # error row — not updated

    def test_update_worddex_silently_ignores_missing_words(self, tmp_path):
        worddex = tmp_path / "worddex.csv"
        src = tmp_path / "cards.csv"
        _write_worddex(worddex, {})
        _write_card_csv(src, [_card_row(word="taberu")])

        p = _FakePipeline(str(src), worddex_csv=str(worddex), filter_known=False, append_all_cards=False, update_worddex=True)
        p._do_update_worddex(str(src))  # must not raise

    # -- run() orchestration ------------------------------------------------

    def test_run_full_flow(self, tmp_path):
        worddex = tmp_path / "worddex.csv"
        all_cards = tmp_path / "all.csv"
        src = tmp_path / "output.csv"
        _write_worddex(worddex, {"suru": 1, "taberu": 0})
        _write_card_csv(src, [_card_row(word="suru"), _card_row(word="taberu")])

        p = _FakePipeline(str(src), worddex_csv=str(worddex), all_cards_csv=str(all_cards))
        result = p.run()

        assert result == "fake.apkg"

        # filter wrote a _filtered.csv; suru is skipped there
        filtered = pd.read_csv(tmp_path / "output_filtered.csv")
        assert filtered.loc[filtered["word"] == "suru", "status"].iloc[0] == "skip"
        assert filtered.loc[filtered["word"] == "taberu", "status"].iloc[0] == "ok"

        # all-cards only has taberu (the ok row from the filtered CSV)
        ac = pd.read_csv(all_cards)
        assert list(ac["word"]) == ["taberu"]

        # worddex updated for taberu only
        wdx = pd.read_csv(worddex, index_col=0)
        assert wdx.loc["taberu", "Anki (word)"] == 1
        assert wdx.loc["suru", "Anki (word)"] == 1   # was already 1
