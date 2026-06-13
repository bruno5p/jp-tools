"""Real end-to-end integration tests.

Run with: pytest --integration

Requires yt-dlp, ffmpeg, and the jp-tools[transcribe] extra installed.
Downloads are cached in tests/integration_data/ so re-runs skip the download step.
"""

import csv
import sqlite3
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
INTEGRATION_DATA = Path(__file__).parent / "integration_data"


def _apkg_note_count(apkg_path: Path) -> int:
    """Extract collection.anki2 from an .apkg and return the number of notes."""
    with zipfile.ZipFile(apkg_path) as zf:
        db_bytes = zf.read("collection.anki2")
    with tempfile.NamedTemporaryFile(suffix=".anki2", delete=False) as tmp_f:
        tmp_f.write(db_bytes)
        tmp_db_path = tmp_f.name
    try:
        conn = sqlite3.connect(tmp_db_path)
        try:
            return conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        finally:
            conn.close()
    finally:
        Path(tmp_db_path).unlink(missing_ok=True)


@pytest.mark.integration
def test_pipeline_anki_from_list():
    """AnkiCardData CSV → .apkg using real dictionaries and real morphology."""
    from jp_tools.pipelines.pipeline_anki import PipelineAnkiFromList

    fixture_csv = FIXTURES / "anki_words_list.csv"
    with open(fixture_csv, encoding="utf-8") as f:
        expected_cards = sum(
            1 for row in csv.DictReader(f) if row.get("word", "").strip()
        )

    INTEGRATION_DATA.mkdir(exist_ok=True)
    output_apkg = INTEGRATION_DATA / "deck.apkg"

    pipeline = PipelineAnkiFromList(
        csv_path=str(fixture_csv),
        output=str(output_apkg),
    )
    result = pipeline.run()

    assert output_apkg.exists(), f".apkg not created at {output_apkg}"
    assert result == str(output_apkg)
    assert _apkg_note_count(output_apkg) == expected_cards

    with zipfile.ZipFile(output_apkg) as zf:
        db_bytes = zf.read("collection.anki2")
    with tempfile.NamedTemporaryFile(suffix=".anki2", delete=False) as tmp_f:
        tmp_f.write(db_bytes)
        tmp_db_path = tmp_f.name
    try:
        conn = sqlite3.connect(tmp_db_path)
        try:
            fields_rows = conn.execute("SELECT flds FROM notes").fetchall()
        finally:
            conn.close()
    finally:
        Path(tmp_db_path).unlink(missing_ok=True)

    for (flds,) in fields_rows:
        main_definition = flds.split("\x1f")[5]
        assert main_definition not in ("(not found)", ""), (
            f"Dictionary lookup failed for a note; MainDefinition={main_definition!r}"
        )


@pytest.mark.integration
def test_pipeline_youtube_transcribe():
    """Word table → download → transcribe → refine → AnkiCardData CSV."""
    from jp_tools.pipelines.models import AnkiCardData
    from jp_tools.pipelines.pipeline_youtube import PipelineYoutubeTranscribe

    INTEGRATION_DATA.mkdir(exist_ok=True)
    segments_dir = INTEGRATION_DATA / "segments"
    segments_dir.mkdir(exist_ok=True)
    output_csv = INTEGRATION_DATA / "output.csv"

    pipeline = PipelineYoutubeTranscribe(
        input_table=str(FIXTURES / "words.csv"),
        output_csv=str(output_csv),
        segments_dir=str(segments_dir),
        interval=8,
    )
    pipeline.run()

    df = pd.read_csv(output_csv)
    assert len(df) == 2
    assert list(df.columns) == list(AnkiCardData.model_fields.keys())
    assert (df["status"] == "ok").all(), (
        f"Some rows failed:\n{df[df['status'] != 'ok'][['word', 'status_message']]}"
    )
    assert df["sentence"].str.len().gt(0).all(), "Expected non-empty sentences"
    assert df["sentence_audio_path"].apply(lambda p: Path(p).exists()).all(), (
        "Refined audio files not found on disk"
    )


@pytest.mark.integration
def test_pipeline_youtube_to_anki():
    """Word table → download → transcribe → refine → .apkg end-to-end."""
    from jp_tools.pipelines.pipeline_youtube import PipelineYoutubeToAnki

    INTEGRATION_DATA.mkdir(exist_ok=True)
    segments_dir = INTEGRATION_DATA / "segments"
    segments_dir.mkdir(exist_ok=True)
    output_apkg = INTEGRATION_DATA / "youtube_deck.apkg"

    pipeline = PipelineYoutubeToAnki(
        input_table=str(FIXTURES / "words.csv"),
        output=str(output_apkg),
        output_csv=str(INTEGRATION_DATA / "output.csv"),
        segments_dir=str(segments_dir),
        interval=8,
    )
    result = pipeline.run()

    assert output_apkg.exists(), f".apkg not created at {output_apkg}"
    assert result == str(output_apkg)

    with open(FIXTURES / "words.csv", encoding="utf-8") as f:
        expected_cards = sum(
            1 for row in csv.DictReader(f) if row.get("word", "").strip()
        )

    assert _apkg_note_count(output_apkg) == expected_cards
