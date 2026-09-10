"""ECoG paradigms: transform raw data into (X, y, metadata)."""

from .base import BaseClassificationParadigm, BaseParadigm, BaseRegressionParadigm
from .classification import (
    EpochedClassification,
    FaceHouseClassification,
    FingerClassification,
    MotorClassification,
    NBackTargetClassification,
    VisualSearchClassification,
)
from .regression import CursorRegression, FingerFlexionRegression

__all__ = [
    "BaseParadigm",
    "BaseClassificationParadigm",
    "BaseRegressionParadigm",
    "EpochedClassification",
    "MotorClassification",
    "FingerClassification",
    "FaceHouseClassification",
    "VisualSearchClassification",
    "NBackTargetClassification",
    "FingerFlexionRegression",
    "CursorRegression",
]
