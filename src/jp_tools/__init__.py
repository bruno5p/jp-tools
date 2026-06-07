"""jp_tools — a collection of composable Japanese-learning tools.

Building blocks live in :mod:`jp_tools.core`; high-level orchestration lives in
:mod:`jp_tools.pipelines`.
"""

__version__ = "0.1.0"

from .pipelines import (  # noqa: E402
    ListCreateAnkiPipeline,
    Pipeline,
    YoutubeCreateAnkiPipeline,
    YoutubeTranscribePipeline,
)

__all__ = [
    "__version__",
    "Pipeline",
    "YoutubeTranscribePipeline",
    "ListCreateAnkiPipeline",
    "YoutubeCreateAnkiPipeline",
]
