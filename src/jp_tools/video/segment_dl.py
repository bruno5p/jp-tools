import os
import shutil
import subprocess

from .._paths import FFMPEG_HINT, YTDLP_HINT

_YTDLP_HINT = str(YTDLP_HINT)
_FFMPEG_HINT = str(FFMPEG_HINT)


class SegmentDownloader:
    def __init__(self, ytdlp=None, ffmpeg=None):
        self.ytdlp = self._find_tool(ytdlp or _YTDLP_HINT, "yt-dlp")
        self.ffmpeg = self._find_tool(ffmpeg or _FFMPEG_HINT, "ffmpeg")

    @staticmethod
    def _find_tool(hint_path, exe_name):
        if hint_path and os.path.isfile(hint_path):
            return hint_path
        found = shutil.which(exe_name)
        if found:
            return found
        raise RuntimeError(f"'{exe_name}' not found. Install it or pass the path explicitly.")

    @staticmethod
    def parse_timestamp(ts):
        ts = ts.strip()
        parts = ts.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        raise ValueError(f"Cannot parse timestamp: {ts!r}  (expected M:SS or H:MM:SS)")

    @staticmethod
    def _seconds_to_hms(s):
        s = int(s)
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{sec:02d}"

    @staticmethod
    def format_label(s):
        s = int(round(s))
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        if h > 0:
            return f"{h}h{m}m{sec}s"
        return f"{m}m{sec}s"

    @staticmethod
    def _segment_filename(index, center):
        return f"segment_{index:03d}_{SegmentDownloader.format_label(center)}.mp3"

    @staticmethod
    def _get_duration(url, ytdlp):
        result = subprocess.run(
            [ytdlp, "--print", "duration", "--no-playlist", url],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())

    @staticmethod
    def _build_ytdlp_cmd(ytdlp, ffmpeg, url, start, end, output_path):
        section = f"*{SegmentDownloader._seconds_to_hms(start)}-{SegmentDownloader._seconds_to_hms(end)}"
        return [
            ytdlp,
            "--download-sections",
            section,
            "-x",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "0",
            "--ffmpeg-location",
            os.path.dirname(ffmpeg),
            "--force-keyframes-at-cuts",
            "--no-playlist",
            "-o",
            output_path,
            url,
        ]

    def download(self, url, timestamps, interval, output_dir):
        half = interval / 2.0

        print("Fetching video duration...")
        try:
            duration = self._get_duration(url, self.ytdlp)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Could not fetch video duration (yt-dlp exit {e.returncode}).") from e
        print(f"Duration: {duration:.1f}s")

        os.makedirs(output_dir, exist_ok=True)
        errors = []
        total = len(timestamps)

        for i, center in enumerate(timestamps, start=1):
            start = max(0.0, center - half)
            end = min(duration, center + half)

            if start >= end:
                print(f"[{i}/{total}] Skipping {self.format_label(center)}: zero-length interval after clamping.")
                continue

            out_file = os.path.join(output_dir, self._segment_filename(i, center))
            if os.path.exists(out_file):
                print(f"[{i}/{total}] Already exists, skipping: {os.path.basename(out_file)}")
                continue

            print(f"[{i}/{total}] {self.format_label(center)}  [{self._seconds_to_hms(start)} -> {self._seconds_to_hms(end)}]  =>  {os.path.basename(out_file)}")
            cmd = self._build_ytdlp_cmd(self.ytdlp, self.ffmpeg, url, start, end, out_file)

            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"  ERROR: yt-dlp failed for segment {i} (exit {e.returncode})")
                errors.append(i)

        if errors:
            raise RuntimeError(f"Failed segments: {errors}")
