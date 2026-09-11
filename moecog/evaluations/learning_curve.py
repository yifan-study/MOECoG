"""Learning curves: how much of a patient's data a pipeline needs (the MOABB ``data_size`` idea, chronological)."""

from __future__ import annotations

import warnings

import numpy as np

from moecog.paradigms.base import BaseRegressionParadigm

from .base import BaseEvaluation


class LearningCurveEvaluation(BaseEvaluation):
    """Train on a growing chronological prefix of each (patient, session), test on the fixed final block.

    The last ``test_fraction`` of the trials (in recording order) is the test set for every point of the
    curve; the training set is the first ``f`` of the remaining trials for each ``f`` in ``fractions``, so a
    small budget means "the earliest few minutes of the session", which is what a calibration phase gives.
    Rows carry ``train_fraction`` and ``n_train``; classification points whose training prefix lacks a class
    are skipped with a warning.

    Parameters
    ----------
    paradigm, datasets, random_state
        See :class:`~moecog.evaluations.base.BaseEvaluation`.
    fractions : sequence of float
        Training fractions of the non-test trials (default 0.1, 0.25, 0.5, 1.0).
    test_fraction : float
        Share of trials held out at the end of every (patient, session) (default 0.2).
    min_train : int
        Smallest training set that is attempted (default 4).
    """

    def __init__(self, paradigm, datasets, random_state=42, fractions=(0.1, 0.25, 0.5, 1.0), test_fraction=0.2,
                 min_train=4):
        super().__init__(paradigm, datasets, n_splits=None, random_state=random_state)
        self.fractions = tuple(float(f) for f in fractions)
        self.test_fraction = float(test_fraction)
        self.min_train = int(min_train)

    @property
    def is_regression(self):
        return isinstance(self.paradigm, BaseRegressionParadigm)

    def _evaluate(self, dataset, X, y, metadata, pipelines):
        results = []
        groups = metadata.groupby(["subject", "session"], sort=False).indices
        for (subject, session), idx in groups.items():
            idx = np.asarray(idx)
            n = len(idx)
            n_test = max(1, int(round(n * self.test_fraction)))
            test = idx[n - n_test:]
            pool = idx[: n - n_test]
            if len(pool) < self.min_train:
                warnings.warn(f"{dataset.code} {subject}/{session}: {n} trials, too few for a learning curve")
                continue
            for frac in self.fractions:
                n_train = max(self.min_train, int(round(len(pool) * frac)))
                n_train = min(n_train, len(pool))
                train = pool[:n_train]
                if not self.is_regression and (len(np.unique(y[train])) < 2 or len(np.unique(y[test])) < 2):
                    warnings.warn(f"{dataset.code} {subject}/{session} fraction {frac}: single class, skipped")
                    continue
                for name, pipeline in pipelines.items():
                    out = self._score_pipeline(pipeline, X[train], y[train], X[test], y[test],
                                               where=f"({name}, {dataset.code} {subject}/{session} fraction {frac})")
                    if out is None:
                        continue
                    for metric, score in out["scores"].items():
                        results.append({
                            "dataset": dataset.code, "subject": subject, "session": session, "pipeline": name,
                            "metric": metric, "score": score, "fold": 0, "fold_policy": "learning_curve",
                            "train_fraction": frac, "n_train": len(train), "n_test": len(test),
                            "n_channels": X.shape[1], "time": out["time"],
                        })
        return results
