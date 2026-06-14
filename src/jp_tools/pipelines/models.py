import re
from datetime import datetime
from typing import Literal

import pandas as pd
from pydantic import BaseModel, field_validator


class AnkiCardData(BaseModel):
    added_on: datetime
    word: str
    reading: str | None = None
    sentence: str | None = None
    word_audio_path: str | None = None
    sentence_audio_path: str | None = None
    picture_path: str | None = None
    definition: str | None = None
    definition_picture_path: str | None = None
    hint: str | None = None
    tags: str | None = None
    source_metadata: str | None = None
    status: Literal["pending", "ok", "error", "skip"] | None = None
    status_message: str | None = None

    def to_csv_row(self) -> dict:
        row = self.model_dump(mode="json")
        return {k: ("" if v is None else v) for k, v in row.items()}

    @classmethod
    def from_csv_row(cls, row: dict) -> "AnkiCardData":
        cleaned = {k: (None if v == "" else v) for k, v in row.items()}
        return cls.model_validate(cleaned)


class YoutubeWordRow(BaseModel):
    video_url: str
    word: str
    timestamp: str
    hint: str = ""

    @field_validator("video_url")
    @classmethod
    def _check_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"Not a valid URL: {v!r}")
        return v

    @field_validator("timestamp")
    @classmethod
    def _check_timestamp(cls, v: str) -> str:
        if not re.match(r"^\d+:\d{2}(:\d{2})?$", v.strip()):
            raise ValueError(f"Invalid timestamp {v!r} — expected mm:ss or hh:mm:ss")
        return v.strip()

    @classmethod
    def from_df(cls, df: pd.DataFrame) -> list["YoutubeWordRow"]:
        return [cls.model_validate(row) for row in df.to_dict("records")]
