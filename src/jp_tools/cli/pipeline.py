"""Console entry point for the transcribe pipeline (jp-pipeline).

Word table → download → transcribe → refine → CSV.
"""

import argparse

from ..pipelines import YoutubeTranscribePipeline
from ..pipelines.youtube_transcribe import DEFAULT_ASR_MODEL


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download, transcribe, and refine YouTube segments from a word table."
    )
    parser.add_argument("input", help="Input table file (TSV, CSV, or Markdown)")
    parser.add_argument("--output", "-o", default="output.csv",
                        help="Output CSV path (default: output.csv)")
    parser.add_argument("--segments-dir", default="segments", metavar="DIR",
                        help="Directory for downloaded segments (default: segments)")
    parser.add_argument("--interval", "-i", type=float, default=8,
                        help="Total clip duration in seconds (default: 8)")
    parser.add_argument("--model", default=DEFAULT_ASR_MODEL, metavar="MODEL_ID",
                        help=f"ASR model ID (default: {DEFAULT_ASR_MODEL})")
    parser.add_argument("--device", default=None, metavar="DEVICE",
                        help="ASR device: 'cuda', 'cpu', etc. (auto-detected if omitted)")
    parser.add_argument("--ytdlp", default=None, metavar="PATH",
                        help="Path to yt-dlp executable (auto-detected if omitted)")
    parser.add_argument("--ffmpeg", default=None, metavar="PATH",
                        help="Path to ffmpeg executable (auto-detected if omitted)")
    args = parser.parse_args()

    YoutubeTranscribePipeline(
        args.input,
        output_csv=args.output,
        segments_dir=args.segments_dir,
        interval=args.interval,
        ytdlp=args.ytdlp,
        ffmpeg=args.ffmpeg,
        model=args.model,
        device=args.device,
    ).run()


if __name__ == "__main__":
    main()
