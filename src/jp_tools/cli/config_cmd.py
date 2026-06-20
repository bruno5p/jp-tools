"""Console entry point for config management (jp-config)."""

import argparse
import sys
from pathlib import Path

_TEMPLATE = """\
[anki]
deck_name     = "Japanese Mining"
output        = "deck.apkg"
word_audio    = true
audio_timeout = 10

[dicts]
daijirin = "dicts/daijirin"
daijisen = "dicts/daijisen"
jmdict   = "dicts/jmdict_english"
pitch    = "dicts/pitch_daijisen"
freq     = [
    "dicts/jpdb_freq",
    "dicts/anime_drama_freq_list",
    "dicts/innocent_ranked",
    "dicts/SoL Top 100",
]

[pipeline]
output       = "output.csv"
segments_dir = "segments"
interval     = 8
model        = "kotoba-tech/kotoba-whisper-v2.2"

[tools]
# ytdlp  = "C:/tools/yt-dlp.exe"
# ffmpeg = "C:/tools/ffmpeg/ffmpeg.exe"

[audio]
local_url = "http://localhost:8770/?expression={expression}&reading={reading}"

[worddex]
# filter_known     = true
# append_all_cards = true
# update_worddex   = true
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage jp-tools configuration.")
    sub = parser.add_subparsers(dest="command")

    init_p = sub.add_parser("init", help="Generate a default jp-tools.toml config file.")
    init_p.add_argument(
        "--output", "-o", default=None, metavar="PATH",
        help="Write config to PATH instead of stdout",
    )

    args = parser.parse_args()

    if args.command == "init":
        if args.output:
            path = Path(args.output)
            if path.exists():
                print(f"Error: {path} already exists. Remove it first.", file=sys.stderr)
                sys.exit(1)
            path.write_text(_TEMPLATE, encoding="utf-8")
            print(f"Config written to {path}")
        else:
            print(_TEMPLATE, end="")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
