"""Console entry point for the transcribe pipeline (jp-pipeline).

Word table → download → transcribe → refine → CSV.
"""

import argparse
from pathlib import Path

from ..config import load_config, resolve_pipeline, resolve_tools
from ..pipelines import PipelineYoutubeTranscribe
from ..pipelines.pipeline_youtube import DEFAULT_ASR_MODEL
from ..table_readers import CsvTableReader


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download, transcribe, and refine YouTube segments from a word table."
    )
    parser.add_argument("input", help="Input table file (TSV, CSV, or Markdown)")
    parser.add_argument("--config", metavar="PATH",
                        help="Path to jp-tools.toml (default: auto-discover)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output CSV path (default: output.csv)")
    parser.add_argument("--segments-dir", default=None, metavar="DIR",
                        help="Directory for downloaded segments (default: segments)")
    parser.add_argument("--interval", "-i", type=float, default=None,
                        help="Total clip duration in seconds (default: 8)")
    parser.add_argument("--model", default=None, metavar="MODEL_ID",
                        help=f"ASR model ID (default: {DEFAULT_ASR_MODEL})")
    parser.add_argument("--device", default=None, metavar="DEVICE",
                        help="ASR device: 'cuda', 'cpu', etc. (auto-detected if omitted)")
    parser.add_argument("--ytdlp", default=None, metavar="PATH",
                        help="Path to yt-dlp executable (auto-detected if omitted)")
    parser.add_argument("--ffmpeg", default=None, metavar="PATH",
                        help="Path to ffmpeg executable (auto-detected if omitted)")
    args = parser.parse_args()

    cfg = load_config(Path(args.config) if args.config else None)
    pipeline = resolve_pipeline(args, cfg)
    tools = resolve_tools(args, cfg)

    PipelineYoutubeTranscribe(
        CsvTableReader(args.input),
        output_csv=pipeline["output_csv"],
        segments_dir=pipeline["segments_dir"],
        interval=pipeline["interval"],
        ytdlp=tools["ytdlp"],
        ffmpeg=tools["ffmpeg"],
        model=pipeline["model"],
        device=args.device,
    ).run()


if __name__ == "__main__":
    main()
