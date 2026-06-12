"""YoutubeCreateAnkiPipeline: word table → (download/transcribe/refine) → Anki deck.

End-to-end composition of :class:`YoutubeTranscribePipeline` (produces the
sentence/audio CSV) followed by :class:`ListCreateAnkiPipeline` (turns that CSV
into an .apkg deck).
"""

from .base import Pipeline
from .list_create_anki import ListCreateAnkiPipeline
from .youtube_transcribe import DEFAULT_ASR_MODEL, YoutubeTranscribePipeline


class YoutubeCreateAnkiPipeline(Pipeline):
    """Build an Anki deck directly from a YouTube word table."""

    def __init__(
        self,
        input_table: str,
        output: str = "deck.apkg",
        deck_name: str = "Japanese Mining",
        output_csv: str = "output.csv",
        segments_dir: str = "segments",
        interval: float = 8,
        ytdlp: str | None = None,
        ffmpeg: str | None = None,
        model: str = DEFAULT_ASR_MODEL,
        device: str | None = None,
        daijirin: str | None = None,
        daijisen: str | None = None,
        jmdict: str | None = None,
        pitch: str | None = None,
        freq: str | None = None,
    ):
        self.transcribe = YoutubeTranscribePipeline(
            input_table,
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
        self.daijirin = daijirin
        self.daijisen = daijisen
        self.jmdict = jmdict
        self.pitch = pitch
        self.freq = freq

    def run(self) -> str:
        csv_path = self.transcribe.run()
        anki = ListCreateAnkiPipeline(
            csv_path,
            output=self.output,
            deck_name=self.deck_name,
            daijirin=self.daijirin,
            daijisen=self.daijisen,
            jmdict=self.jmdict,
            pitch=self.pitch,
            freq=self.freq,
        )
        return anki.run()
