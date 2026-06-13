from datetime import datetime
from typing import Literal

from pydantic import BaseModel


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
