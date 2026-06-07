"""Real end-to-end integration tests.

Run with: pytest --integration

Requires yt-dlp, ffmpeg, and the jp-tools[transcribe] extra installed.
Downloads are cached in tests/integration_data/ so re-runs skip the download step.
"""

from pathlib import Path

import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
INTEGRATION_DATA = Path(__file__).parent / "integration_data"


@pytest.mark.integration
def test_full_pipeline():
    from jp_tools.pipelines.youtube_transcribe import YoutubeTranscribePipeline

    segments_dir = INTEGRATION_DATA / "segments"
    output_csv = INTEGRATION_DATA / "output.csv"
    INTEGRATION_DATA.mkdir(exist_ok=True)
    segments_dir.mkdir(exist_ok=True)

    pipeline = YoutubeTranscribePipeline(
        input_table=str(FIXTURES / "words.csv"),
        output_csv=str(output_csv),
        segments_dir=str(segments_dir),
        interval=8,
    )
    pipeline.run()

    df = pd.read_csv(output_csv)
    assert len(df) == 2
    assert list(df.columns) == ["video_url", "timestamp", "word", "sentence", "ref_audio_path", "status", "status_message"]
    assert (df["status"] == "ok").all(), f"Some rows failed:\n{df[df['status'] != 'ok'][['word', 'status_message']]}"
    assert df["sentence"].str.len().gt(0).all(), "Expected non-empty sentences"
    assert df["ref_audio_path"].apply(lambda p: Path(p).exists()).all(), "Refined audio files not found on disk"
