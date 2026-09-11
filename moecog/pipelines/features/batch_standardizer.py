"""Per-batch feature standardisation: the label-free session fix for band-power pipelines."""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class BatchStandardizer(BaseEstimator, TransformerMixin):
    """Z-score every feature over the batch being transformed, not over the training set.

    ``fit`` records the training statistics only for reference; ``transform`` standardises the batch it is given
    with that batch's own mean and standard deviation. In a cross-session evaluation the test batch is the whole
    held-out session, so this is per-session feature standardisation without labels: the operation a deployed
    decoder can do on a new day after collecting a few minutes of unlabeled data. Within a session it acts on a
    test fold (a fifth of the session), which is the same thing at a smaller scale. Put it after the feature
    extractor (``LogBandPower -> BatchStandardizer -> LDA``).

    Parameters
    ----------
    min_batch : int
        Below this many samples the training statistics are used instead (a lone trial cannot be standardised).
    eps : float
    """

    def __init__(self, min_batch=8, eps=1e-12):
        self.min_batch = min_batch
        self.eps = eps

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float).reshape(len(X), -1)
        self.mean_ = X.mean(axis=0)
        self.scale_ = X.std(axis=0) + self.eps
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float).reshape(len(X), -1)
        if len(X) < self.min_batch:
            return (X - self.mean_) / self.scale_
        return (X - X.mean(axis=0)) / (X.std(axis=0) + self.eps)
