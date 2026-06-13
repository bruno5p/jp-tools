"""Yomitan-style Japanese dictionary lookup (deinflection + POS-gated matching).

Pure-Python and dependency-free; importable without fugashi.
"""

from .dictionary import DictResult, DictionarySet, get_dict
from .japanese_transforms import JAPANESE_TRANSFORMER
from .transforms import LanguageTransformer

__all__ = [
    "DictResult",
    "DictionarySet",
    "get_dict",
    "JAPANESE_TRANSFORMER",
    "LanguageTransformer",
]
