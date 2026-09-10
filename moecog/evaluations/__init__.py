"""Evaluation strategies for ECoG benchmarking."""

from .base import BaseEvaluation, compute_metric
from .within_subject import WithinSubjectCV, contiguous_folds

__all__ = ["BaseEvaluation", "WithinSubjectCV", "compute_metric", "contiguous_folds"]
