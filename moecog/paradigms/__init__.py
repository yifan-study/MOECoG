"""ECoG paradigms — transform raw data into (X, y, metadata)."""

from .base import BaseClassificationParadigm, BaseParadigm, BaseRegressionParadigm

__all__ = [
    "BaseParadigm",
    "BaseClassificationParadigm",
    "BaseRegressionParadigm",
]
