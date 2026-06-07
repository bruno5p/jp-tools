"""Centralized path resolution for the jp_tools package.

Resolving these once here keeps the fragile ``parents[N]`` arithmetic out of the
individual modules, which live at varying depths (``core/``, ``pipelines/``).
"""

from pathlib import Path

# …/jp-tools/src/jp_tools
PACKAGE_ROOT = Path(__file__).resolve().parent
# …/jp-tools  (repo root)
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
# …/Japanese Tools  (where sibling tool folders like youtube-dl / Subs2SRS live)
TOOLS_DIR = PROJECT_ROOT.parent

# Default location for user-supplied Yomitan dictionary ZIPs.
DEFAULT_DICTS_DIR = PROJECT_ROOT / "dicts"

# External tool hints (Windows). _find_tool falls back to PATH via shutil.which.
YTDLP_HINT = TOOLS_DIR / "youtube-dl" / "yt-dlp.exe"
FFMPEG_HINT = TOOLS_DIR / "Subs2SRS" / "Utils" / "ffmpeg" / "ffmpeg.exe"
