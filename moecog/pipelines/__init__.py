"""Pipelines: feature extractors, decoders, and reference baselines."""

from __future__ import annotations

from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import HighGammaPower, LogBandPower


def _shrinkage_lda():
    return LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")


def classification_baselines(sfreq=1000.0):
    """Reference classical pipelines for the epoched paradigms."""
    return {
        "LogBandPower+LDA": make_pipeline(
            LogBandPower(sfreq=sfreq), StandardScaler(), _shrinkage_lda()
        ),
        "LogBandPower+LogReg": make_pipeline(
            LogBandPower(sfreq=sfreq), StandardScaler(), LogisticRegression(max_iter=2000)
        ),
        "HighGamma+LDA": make_pipeline(
            HighGammaPower(sfreq=sfreq), StandardScaler(), _shrinkage_lda()
        ),
    }


def regression_baselines(sfreq=1000.0):
    """Reference classical pipelines for the continuous paradigms."""
    return {
        "LogBandPower+Ridge": make_pipeline(
            LogBandPower(sfreq=sfreq), StandardScaler(), Ridge(alpha=1.0)
        ),
        "HighGamma+Ridge": make_pipeline(
            HighGammaPower(sfreq=sfreq), StandardScaler(), Ridge(alpha=1.0)
        ),
    }


__all__ = ["LogBandPower", "HighGammaPower", "classification_baselines", "regression_baselines"]
