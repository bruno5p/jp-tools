"""Base class for composable jp_tools pipelines."""

from abc import ABC, abstractmethod
from typing import Any


class Pipeline(ABC):
    """A pipeline bundles a sequence of building-block steps behind one entry point.

    Subclasses take their configuration in ``__init__`` (paths, options) and do
    the work in :meth:`run`, composing functions from :mod:`jp_tools.core` and/or
    other pipelines. ``run`` should return its primary output (e.g. the path of a
    produced file) so pipelines can be chained.
    """

    @abstractmethod
    def run(self) -> Any:
        """Execute the pipeline and return its primary output."""
        raise NotImplementedError
