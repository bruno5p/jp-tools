import os
import re
import shutil
import subprocess

from .._paths import FFMPEG_HINT

_FFMPEG_HINT = str(FFMPEG_HINT)


class SegmentRefiner:
    def __init__(self, ffmpeg=None):
        self.ffmpeg = self._find_tool(ffmpeg or _FFMPEG_HINT, "ffmpeg")

    @staticmethod
    def _find_tool(hint, exe):
        if hint and os.path.isfile(hint):
            return hint
        found = shutil.which(exe)
        if found:
            return found
        raise RuntimeError(f"'{exe}' not found. Install it or pass the path explicitly.")

    @staticmethod
    def _get_audio_duration(path, ffmpeg):
        r = subprocess.run([ffmpeg, "-i", path], capture_output=True, text=True)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stderr)
        if not m:
            raise RuntimeError(f"Could not parse duration from ffmpeg output for: {path}")
        h, mn, s = m.groups()
        return int(h) * 3600 + int(mn) * 60 + float(s)

    @staticmethod
    def _parse_sub_timestamp(ts):
        ts = ts.strip().replace(",", ".")
        m = re.match(r"(\d+):(\d+):(\d+)\.(\d+)", ts)
        if not m:
            raise ValueError(f"Bad subtitle timestamp: {ts!r}")
        h, mn, s, frac = m.groups()
        return int(h) * 3600 + int(mn) * 60 + int(s) + float(f"0.{frac}")

    @staticmethod
    def _parse_srt_vtt(content):
        subs = []
        for m in re.finditer(r"(\d+:\d+:\d+[,\.]\d+)\s*-->\s*(\d+:\d+:\d+[,\.]\d+)", content):
            try:
                subs.append((SegmentRefiner._parse_sub_timestamp(m.group(1)), SegmentRefiner._parse_sub_timestamp(m.group(2))))
            except ValueError:
                continue
        return subs

    @staticmethod
    def _parse_ass(content):
        subs = []
        for m in re.finditer(
            r"^Dialogue:[^,]*,(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+)",
            content, re.MULTILINE,
        ):
            try:
                subs.append((SegmentRefiner._parse_sub_timestamp(m.group(1)), SegmentRefiner._parse_sub_timestamp(m.group(2))))
            except ValueError:
                continue
        return subs

    @staticmethod
    def _load_subtitles(path):
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            content = f.read()
        if os.path.splitext(path)[1].lower() in (".ass", ".ssa"):
            return SegmentRefiner._parse_ass(content)
        return SegmentRefiner._parse_srt_vtt(content)

    @staticmethod
    def _find_closest_subtitle(subs, target):
        containing = [(s, e) for s, e in subs if s <= target <= e]
        pool = containing if containing else subs
        return min(pool, key=lambda se: abs((se[0] + se[1]) / 2 - target))

    @staticmethod
    def _cut_audio(ffmpeg, input_path, rel_start, rel_end, output_path):
        subprocess.run([
            ffmpeg, "-y",
            "-i", input_path,
            "-ss", f"{rel_start:.3f}",
            "-to", f"{rel_end:.3f}",
            output_path,
        ], check=True)

    def refine(self, audio_path, padding=0.25) -> str:
        """Trim audio to the subtitle line closest to its midpoint. Returns refined path."""
        stem = os.path.splitext(audio_path)[0]
        refined_path = stem + "_refined.mp3"
        if os.path.exists(refined_path):
            return refined_path

        srt_path = stem + ".srt"
        if not os.path.isfile(srt_path):
            raise FileNotFoundError(f"No subtitles found for refine: {srt_path}")
        subs = self._load_subtitles(srt_path)
        if not subs:
            raise RuntimeError(f"No subtitles parsed from {srt_path}")

        duration = self._get_audio_duration(audio_path, self.ffmpeg)
        target = duration / 2
        sub_start, sub_end = self._find_closest_subtitle(subs, target)
        rel_start = max(0.0, sub_start - padding)
        rel_end = min(duration, sub_end + padding)
        self._cut_audio(self.ffmpeg, audio_path, rel_start, rel_end, refined_path)
        return refined_path
