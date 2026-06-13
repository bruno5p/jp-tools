"""Lightweight smoke tests — no network, no models, no heavy deps."""

from pathlib import Path

import pytest

WORDS_CSV = Path(__file__).parent / "fixtures" / "words.csv"


# --- pure building-block helpers -------------------------------------------

def test_parse_timestamp():
    from jp_tools.video.segment_dl import SegmentDownloader
    assert SegmentDownloader.parse_timestamp("5:40") == 5 * 60 + 40
    assert SegmentDownloader.parse_timestamp("1:02:03") == 3600 + 2 * 60 + 3


def test_format_label():
    from jp_tools.video.segment_dl import SegmentDownloader
    assert SegmentDownloader.format_label(340) == "5m40s"
    assert SegmentDownloader.format_label(3723) == "1h2m3s"


def test_render_pitch_html_heiban():
    from jp_tools.anki.pitch_renderer import render_pitch_html
    html = render_pitch_html("こころ", 0)
    assert "pitch" in html
    assert "title='[0]'" in html


def test_render_pitch_html_none():
    from jp_tools.anki.pitch_renderer import render_pitch_html
    assert render_pitch_html("あい", None) == "<span class='pitch'>あい</span>"
    assert render_pitch_html("", 1) == ""


# --- package / pipeline importability --------------------------------------

def test_top_level_imports():
    import jp_tools
    assert jp_tools.__version__

    from jp_tools.pipelines import (
        ListCreateAnkiPipeline,
        Pipeline,
        YoutubeCreateAnkiPipeline,
        YoutubeTranscribePipeline,
    )
    assert issubclass(YoutubeTranscribePipeline, Pipeline)
    assert issubclass(ListCreateAnkiPipeline, Pipeline)
    assert issubclass(YoutubeCreateAnkiPipeline, Pipeline)


def test_pipeline_construction_no_run():
    """Pipelines construct without importing heavy deps or doing I/O."""
    from jp_tools.pipelines import (
        ListCreateAnkiPipeline,
        YoutubeCreateAnkiPipeline,
        YoutubeTranscribePipeline,
    )
    YoutubeTranscribePipeline(str(WORDS_CSV))
    ListCreateAnkiPipeline(str(WORDS_CSV))
    YoutubeCreateAnkiPipeline(str(WORDS_CSV))


# --- yomitan deinflection: pure Python, no heavy deps -----------------------

def test_deinflection_reaches_dictionary_form():
    from jp_tools.lookup import JAPANESE_TRANSFORMER

    def base_forms(word):
        return {t.text for t in JAPANESE_TRANSFORMER.transform(word)}

    assert "食べる" in base_forms("食べたくない")
    assert "飲む" in base_forms("飲んだ")
    assert "高い" in base_forms("高くない")
    # The dictionary form itself is always among the candidates.
    assert "食べる" in base_forms("食べる")


# --- optional deps: only import if installed --------------------------------

def test_furigana_optional():
    pytest.importorskip("fugashi")
    from jp_tools.furigana import get_furigana_plain, get_sentence_furigana
    assert callable(get_sentence_furigana)
    assert get_furigana_plain("日本語", "にほんご") == "日本語[にほんご]"
    assert get_furigana_plain("ねこ", "ねこ") == "ねこ"
