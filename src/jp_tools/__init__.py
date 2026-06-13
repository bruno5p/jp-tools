"""jp_tools — a collection of composable Japanese-learning tools.

Domain packages: :mod:`jp_tools.anki`, :mod:`jp_tools.video`, :mod:`jp_tools.lookup`.
High-level orchestration lives in :mod:`jp_tools.pipelines`.
"""

__version__ = "0.1.0"

from .pipelines import (  # noqa: E402
    AnkiCardData,
    Pipeline,
    PipelineAnkiFromList,
    YoutubeCreateAnkiPipeline,
    YoutubeTranscribePipeline,
)

__all__ = [
    "__version__",
    "Pipeline",
    "AnkiCardData",
    "YoutubeTranscribePipeline",
    "PipelineAnkiFromList",
    "YoutubeCreateAnkiPipeline",
]
