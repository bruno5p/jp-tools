# jp-tools

Composable Japanese-learning tools: YouTube sentence mining, transcription, and
Anki deck creation. Building blocks live in `jp_tools.core`; high-level
orchestration lives in `jp_tools.pipelines`.

## Install

```bash
pip install -e .                  # core tools (fugashi, jaconv, genanki)
pip install -e '.[transcribe]'    # + ASR stack (torch, transformers) — multi-GB
```

External tools `yt-dlp` and `ffmpeg` must be on `PATH` (or pass `--ytdlp` /
`--ffmpeg`). User-supplied Yomitan dictionaries go in `dicts/`, each extracted
into its own folder (e.g. `dicts/daijirin/`, `dicts/pitch_daijisen/`,
`dicts/jpdb_freq/`) containing the dictionary's `term_bank_*.json` /
`term_meta_bank_*.json` files.

## Command-line tools

| Command           | Description                                                 |
| ----------------- | ----------------------------------------------------------- |
| `jp-pipeline`     | Word table → download → transcribe → refine → CSV           |
| `jp-anki`         | CSV (word/sentence/audio) → Anki deck (`.apkg`)             |
| `jp-youtube-anki` | End-to-end: word table → … → Anki deck                      |
| `jp-segment-dl`   | Download MP3 segments from a YouTube video around timestamps|
| `jp-transcribe`   | Transcribe audio with kotoba-whisper (needs `[transcribe]`) |
| `jp-refine`       | Trim audio segments to subtitle boundaries                  |

The input table (TSV/CSV/Markdown) needs columns: `video_url`, `timestamp`,
`word`. See `tests/words.csv` for an example.

```bash
jp-youtube-anki tests/words.csv -o deck.apkg
```

## Python API

```python
from jp_tools import YoutubeCreateAnkiPipeline

YoutubeCreateAnkiPipeline(
    "words.csv",
    output="deck.apkg",
    segments_dir="segments",
).run()
```

Pipelines compose building blocks behind a single `run()` and can be chained
(`YoutubeCreateAnkiPipeline` = `YoutubeTranscribePipeline` →
`ListCreateAnkiPipeline`). New pipelines subclass `jp_tools.pipelines.Pipeline`.

## Tests

```bash
pytest tests/
```
