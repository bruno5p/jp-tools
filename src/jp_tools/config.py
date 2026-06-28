"""Configuration model and loaders for jp-tools.

Priority chain (lowest → highest):
  built-in defaults < ~/.config/jp-tools/config.toml < jp-tools.toml in CWD
  < --config PATH < individual CLI arguments
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel

# --- Public constants (shared with creator.py) ---

# This ID was the original value chosen to match the "Lapis" note type already
# present in the target Anki collection.  Do not change it without also
# migrating existing notes.
ANKI_MODEL_ID = 1667218449922

# Frequency lists shown on each card, in display order.
DEFAULT_FREQ_NAMES: tuple[str, ...] = (
    "jpdb_freq",
    "anime_drama_freq_list",
    "innocent_ranked",
    "SoL Top 100",
)

# Definition dictionaries tried in order; first folder(s) found are used.
DEFAULT_DICT_NAMES: tuple[str, ...] = ("daijirin", "daijisen", "jmdict_english")
DEFAULT_PITCH_NAME = "pitch_daijisen"

# --- Private scalar defaults ---
_DEFAULT_DECK_NAME = "Japanese Mining"
_DEFAULT_ANKI_OUTPUT = "deck.apkg"
_DEFAULT_WORD_AUDIO = True
_DEFAULT_AUDIO_TIMEOUT = 10.0
_DEFAULT_PIPELINE_OUTPUT = "output.csv"
_DEFAULT_SEGMENTS_DIR = "segments"
_DEFAULT_INTERVAL = 8.0
_DEFAULT_ASR_MODEL = "kotoba-tech/kotoba-whisper-v2.2"
_DEFAULT_LOCAL_AUDIO_URL = (
    "http://localhost:8770/?expression={expression}&reading={reading}"
)
_DEFAULT_FILTER_KNOWN = True
_DEFAULT_APPEND_ALL_CARDS = True
_DEFAULT_UPDATE_WORDDEX = True

# --- Config discovery paths ---
_CWD_CONFIG = Path("jp-tools.toml")
_USER_CONFIG = Path.home() / ".config" / "jp-tools" / "config.toml"


# --- Pydantic sub-models (all fields Optional, all default None) ---


class AnkiConfig(BaseModel):
    deck_name: str | None = None
    output: str | None = None
    word_audio: bool | None = None
    audio_timeout: float | None = None


class DictsConfig(BaseModel):
    dir: str | None = None
    names: list[str] | None = None
    pitch_name: str | None = None
    freq_names: list[str] | None = None


class PipelineConfig(BaseModel):
    output: str | None = None
    segments_dir: str | None = None
    interval: float | None = None
    model: str | None = None


class ToolsConfig(BaseModel):
    ytdlp: str | None = None
    ffmpeg: str | None = None


class AudioConfig(BaseModel):
    local_url: str | None = None


class WorddexConfig(BaseModel):
    filter_known: bool | None = None
    append_all_cards: bool | None = None
    update_worddex: bool | None = None


class JpToolsConfig(BaseModel):
    anki: AnkiConfig = AnkiConfig()
    dicts: DictsConfig = DictsConfig()
    pipeline: PipelineConfig = PipelineConfig()
    tools: ToolsConfig = ToolsConfig()
    audio: AudioConfig = AudioConfig()
    worddex: WorddexConfig = WorddexConfig()


# --- Loaders ---


def load_config(explicit: Path | None = None) -> JpToolsConfig:
    """Load config from explicit path, CWD jp-tools.toml, or user-level config.

    When *explicit* is given, only that path is tried.
    Otherwise checks CWD first, then the user-level config.
    Returns an all-None config (use built-in defaults everywhere) if no file is found.
    """
    candidates = [explicit] if explicit is not None else [_CWD_CONFIG, _USER_CONFIG]
    for path in candidates:
        if path.is_file():
            with open(path, "rb") as f:
                data = tomllib.load(f)
            return JpToolsConfig.model_validate(data)
    return JpToolsConfig()


# --- Helpers ---


def _first(*values):
    """Return the first non-None value in *values* (or the last value if all are None)."""
    for v in values:
        if v is not None:
            return v
    return values[-1]


# --- Resolvers (CLI args > config > built-in default) ---


def resolve_anki(args, cfg: JpToolsConfig) -> dict:
    return {
        "deck_name": _first(
            getattr(args, "deck", None), cfg.anki.deck_name, _DEFAULT_DECK_NAME
        ),
        "output": _first(
            getattr(args, "output", None), cfg.anki.output, _DEFAULT_ANKI_OUTPUT
        ),
        "word_audio": _first(
            getattr(args, "word_audio", None), cfg.anki.word_audio, _DEFAULT_WORD_AUDIO
        ),
        "audio_timeout": _first(
            getattr(args, "audio_timeout", None),
            cfg.anki.audio_timeout,
            _DEFAULT_AUDIO_TIMEOUT,
        ),
    }


def resolve_dicts(args, cfg: JpToolsConfig) -> dict:
    # Leave as None when unset — AnkiCardCreator applies DEFAULT_DICT_NAMES / DEFAULT_DICTS_DIR
    return {
        "dicts_dir": _first(getattr(args, "dicts_dir", None), cfg.dicts.dir),
        "dict_names": _first(getattr(args, "dict_names", None), cfg.dicts.names),
        "pitch_name": _first(getattr(args, "pitch_name", None), cfg.dicts.pitch_name),
        "freq_names": _first(getattr(args, "freq_names", None), cfg.dicts.freq_names),
    }


def resolve_pipeline(args, cfg: JpToolsConfig) -> dict:
    return {
        "output_csv": _first(
            getattr(args, "output", None), cfg.pipeline.output, _DEFAULT_PIPELINE_OUTPUT
        ),
        "segments_dir": _first(
            getattr(args, "segments_dir", None),
            cfg.pipeline.segments_dir,
            _DEFAULT_SEGMENTS_DIR,
        ),
        "interval": _first(
            getattr(args, "interval", None), cfg.pipeline.interval, _DEFAULT_INTERVAL
        ),
        "model": _first(
            getattr(args, "model", None), cfg.pipeline.model, _DEFAULT_ASR_MODEL
        ),
    }


def resolve_tools(args, cfg: JpToolsConfig) -> dict:
    # None is valid — downstream tool finders handle auto-detection
    return {
        "ytdlp": _first(getattr(args, "ytdlp", None), cfg.tools.ytdlp),
        "ffmpeg": _first(getattr(args, "ffmpeg", None), cfg.tools.ffmpeg),
    }


def resolve_worddex(args, cfg: JpToolsConfig) -> dict:
    return {
        "filter_known": _first(
            getattr(args, "filter_known", None),
            cfg.worddex.filter_known,
            _DEFAULT_FILTER_KNOWN,
        ),
        "append_all_cards": _first(
            getattr(args, "append_all_cards", None),
            cfg.worddex.append_all_cards,
            _DEFAULT_APPEND_ALL_CARDS,
        ),
        "update_worddex": _first(
            getattr(args, "update_worddex", None),
            cfg.worddex.update_worddex,
            _DEFAULT_UPDATE_WORDDEX,
        ),
    }
