"""Within-subject cross-validation."""

from __future__ import annotations

import math
import warnings

import numpy as np
from sklearn.model_selection import StratifiedKFold

from moecog.paradigms.base import BaseRegressionParadigm

from .base import BaseEvaluation


def contiguous_folds(n, n_splits):
    """Yield ``(train_idx, test_idx)`` for chronological, contiguous test blocks."""
    edges = np.linspace(0, n, n_splits + 1).astype(int)
    for k in range(n_splits):
        test = np.arange(edges[k], edges[k + 1])
        train = np.concatenate([np.arange(0, edges[k]), np.arange(edges[k + 1], n)])
        yield train, test


class WithinSubjectCV(BaseEvaluation):
    """K-fold cross-validation within each (subject, session).

    Regression data always use **chronological contiguous folds** with a
    purge gap: windows overlap, so shuffled folds leak nearly identical
    samples between train and test. Classification data use contiguous
    chronological trial blocks by default (robust to slow non-stationarity);
    ``shuffle=True`` switches to a stratified shuffled K-fold, the MOABB
    convention.

    Parameters
    ----------
    paradigm, datasets, n_splits, random_state
        See :class:`~moecog.evaluations.base.BaseEvaluation`.
    shuffle : bool
        Shuffled stratified folds for classification (ignored for regression).
    purge : int or None
        Number of windows dropped from the training set on each side of the
        test block (regression). None derives it from the paradigm's window
        overlap: ``ceil(window_size / window_stride) - 1``.
    """

    def __init__(self, paradigm, datasets, n_splits=5, shuffle=False, random_state=42,
                 purge=None):
        super().__init__(paradigm, datasets, n_splits=n_splits, random_state=random_state)
        self.shuffle = shuffle
        self.purge = purge

    @property
    def is_regression(self):
        return isinstance(self.paradigm, BaseRegressionParadigm)

    def _purge(self):
        if self.purge is not None:
            return int(self.purge)
        if self.is_regression:
            return max(0, math.ceil(self.paradigm.window_size / self.paradigm.window_stride) - 1)
        return 0

    def _folds(self, y):
        n = len(y)
        if self.is_regression or not self.shuffle:
            yield from contiguous_folds(n, self.n_splits)
        else:
            skf = StratifiedKFold(self.n_splits, shuffle=True, random_state=self.random_state)
            yield from skf.split(np.zeros(n), y)

    def _evaluate(self, dataset, X, y, metadata, pipelines):
        results = []
        purge = self._purge()
        groups = metadata.groupby(["subject", "session"], sort=False).indices
        for (subject, session), idx in groups.items():
            idx = np.asarray(idx)
            X_s, y_s = X[idx], y[idx]
            if len(idx) < self.n_splits:
                warnings.warn(
                    f"{dataset.code} {subject}/{session}: only {len(idx)} samples, skipped"
                )
                continue
            for fold, (train, test) in enumerate(self._folds(y_s)):
                if purge > 0:
                    lo, hi = test.min() - purge, test.max() + purge
                    train = train[(train < lo) | (train > hi)]
                if not self.is_regression and len(np.unique(y_s[train])) < 2:
                    warnings.warn(
                        f"{dataset.code} {subject}/{session} fold {fold}: one class in train"
                    )
                    continue
                for name, pipeline in pipelines.items():
                    out = self._score_pipeline(
                        pipeline, X_s[train], y_s[train], X_s[test], y_s[test]
                    )
                    for metric, score in out["scores"].items():
                        results.append({
                            "dataset": dataset.code,
                            "subject": subject,
                            "session": session,
                            "pipeline": name,
                            "metric": metric,
                            "score": score,
                            "fold": fold,
                            "n_train": len(train),
                            "n_test": len(test),
                            "n_channels": X_s.shape[1],
                            "time": out["time"],
                        })
        return results
