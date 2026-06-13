"""High-level, composable orchestration pipelines.

Each pipeline subclasses :class:`Pipeline` and wires together building blocks
from :mod:`jp_tools.core` (and/or other pipelines) behind a single ``run()``.

To add a new pipeline, create a module here with a ``Pipeline`` subclass and
export it below.
"""

from .base import Pipeline
from .models import AnkiCardData
from .pipeline_anki_list import PipelineAnkiFromList
from .youtube_create_anki import YoutubeCreateAnkiPipeline
from .youtube_transcribe import YoutubeTranscribePipeline

__all__ = [
    "Pipeline",
    "AnkiCardData",
    "YoutubeTranscribePipeline",
    "PipelineAnkiFromList",
    "YoutubeCreateAnkiPipeline",
]
