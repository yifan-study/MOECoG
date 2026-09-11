"""Evaluation strategies for ECoG benchmarking."""

from .base import BaseEvaluation, compute_metric
from .cross_session import CrossSessionEvaluation
from .learning_curve import LearningCurveEvaluation
from .within_subject import WithinSubjectCV, contiguous_folds

__all__ = ["BaseEvaluation", "WithinSubjectCV", "CrossSessionEvaluation", "LearningCurveEvaluation", "compute_metric",
           "contiguous_folds"]
