"""Real end-to-end integration tests.

Run with: pytest --integration

Requires yt-dlp, ffmpeg, and the jp-tools[transcribe] extra installed.
Downloads are cached in tests/integration_data/ so re-runs skip the download step.
"""

import csv
import sqlite3
import zipfile
from pathlib import Path

import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
INTEGRATION_DATA = Path(__file__).parent / "integration_data"


# @pytest.mark.integration
# def test_full_pipeline():
#     from jp_tools.pipelines.youtube_transcribe import YoutubeTranscribePipeline

#     segments_dir = INTEGRATION_DATA / "segments"
#     output_csv = INTEGRATION_DATA / "output.csv"
#     INTEGRATION_DATA.mkdir(exist_ok=True)
#     segments_dir.mkdir(exist_ok=True)

#     pipeline = YoutubeTranscribePipeline(
#         input_table=str(FIXTURES / "words.csv"),
#         output_csv=str(output_csv),
#         segments_dir=str(segments_dir),
#         interval=8,
#     )
#     pipeline.run()

#     df = pd.read_csv(output_csv)
#     assert len(df) == 2
#     from jp_tools.pipelines.models import AnkiCardData
#     assert list(df.columns) == list(AnkiCardData.model_fields.keys())
#     assert (df["status"] == "ok").all(), (
#         f"Some rows failed:\n{df[df['status'] != 'ok'][['word', 'status_message']]}"
#     )
#     assert df["sentence"].str.len().gt(0).all(), "Expected non-empty sentences"
#     assert df["sentence_audio_path"].apply(lambda p: Path(p).exists()).all(), (
#         "Refined audio files not found on disk"
#     )


@pytest.mark.integration
def test_pipeline_anki_from_list():
    """End-to-end: CSV → .apkg using real dictionaries and real morphology (fugashi)."""
    import tempfile

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

    # Extract collection.anki2 from the .apkg zip into a temp file for SQLite queries
    with zipfile.ZipFile(output_apkg) as zf:
        db_bytes = zf.read("collection.anki2")

    with tempfile.NamedTemporaryFile(suffix=".anki2", delete=False) as tmp_f:
        tmp_f.write(db_bytes)
        tmp_db_path = tmp_f.name

    try:
        conn = sqlite3.connect(tmp_db_path)
        try:
            note_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            # flds stores field values separated by \x1f; MainDefinition is field index 5
            fields_rows = conn.execute("SELECT flds FROM notes").fetchall()
        finally:
            conn.close()
    finally:
        Path(tmp_db_path).unlink(missing_ok=True)

    assert note_count == expected_cards, f"Expected {expected_cards} notes, got {note_count}"

    for (flds,) in fields_rows:
        main_definition = flds.split("\x1f")[5]
        assert main_definition not in ("(not found)", ""), (
            f"Dictionary lookup failed for a note; MainDefinition={main_definition!r}"
        )
