"""High-level, composable orchestration pipelines.

Each pipeline subclasses :class:`Pipeline` and wires together building blocks
from :mod:`jp_tools.core` (and/or other pipelines) behind a single ``run()``.

To add a new pipeline, create a module here with a ``Pipeline`` subclass and
export it below.
"""

from .base import Pipeline
from .models import AnkiCardData, YoutubeWordRow
from .pipeline_anki import PipelineAnkiFromList
from .pipeline_youtube import PipelineYoutubeToAnki, PipelineYoutubeTranscribe

__all__ = [
    "Pipeline",
    "AnkiCardData",
    "YoutubeWordRow",
    "PipelineAnkiFromList",
    "PipelineYoutubeTranscribe",
    "PipelineYoutubeToAnki",
]
