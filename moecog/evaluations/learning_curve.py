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
    Rows carry ``train_fraction`` and ``n_train``.

    Files that present their cues in blocks (all of one class, then all of another) have a single-class final
    block; with ``fallback="stratified"`` (default) those get a stratified shuffled test block and a
    class-interleaved training order instead, marked ``fold_policy="learning_curve_stratified"``. With
    ``fallback=None`` such files are skipped with a warning.

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
    fallback : {"stratified", None}
    """

    def __init__(self, paradigm, datasets, random_state=42, fractions=(0.1, 0.25, 0.5, 1.0), test_fraction=0.2,
                 min_train=4, fallback="stratified", alignment=None):
        super().__init__(paradigm, datasets, n_splits=None, random_state=random_state, alignment=alignment)
        self.fractions = tuple(sorted(float(f) for f in fractions))
        self.test_fraction = float(test_fraction)
        self.min_train = int(min_train)
        if fallback not in ("stratified", None):
            raise ValueError("fallback must be 'stratified' or None")
        self.fallback = fallback

    @property
    def is_regression(self):
        return isinstance(self.paradigm, BaseRegressionParadigm)

    def _n_train(self, n_pool, frac):
        return min(n_pool, max(self.min_train, int(round(n_pool * frac))))

    def _purge(self):
        """Windows dropped before the test block for regression, where windows overlap (as WithinSubjectCV)."""
        if not self.is_regression:
            return 0
        par = self.paradigm
        return max(0, int(np.ceil(par.window_size / par.window_stride)) - 1)

    def _chronological(self, n):
        n_test = max(1, int(round(n * self.test_fraction)))
        idx = np.arange(n)
        return idx[: max(0, n - n_test - self._purge())], idx[n - n_test:]

    def _usable(self, y, pool, test):
        """Every training prefix and the test block hold at least two classes."""
        if self.is_regression:
            return True
        smallest = pool[: self._n_train(len(pool), self.fractions[0])]
        return len(np.unique(y[test])) >= 2 and len(np.unique(y[smallest])) >= 2

    def _stratified(self, y):
        """Stratified shuffled test block; the pool ordered by interleaving the classes."""
        rng = np.random.default_rng(self.random_state)
        classes = np.unique(y)
        per_class = {c: rng.permutation(np.flatnonzero(y == c)) for c in classes}
        test, pools = [], {}
        for c, members in per_class.items():
            k = max(1, int(round(len(members) * self.test_fraction)))
            test.extend(members[:k])
            pools[c] = list(members[k:])
        pool = []
        while any(pools.values()):
            for c in classes:
                if pools[c]:
                    pool.append(pools[c].pop(0))
        return np.asarray(pool, dtype=int), np.asarray(sorted(test), dtype=int)

    def _evaluate(self, dataset, X, y, metadata, pipelines):
        results = []
        groups = metadata.groupby(["subject", "session"], sort=False).indices
        for (subject, session), idx in groups.items():
            idx = np.asarray(idx)
            n = len(idx)
            X_s, y_s = X[idx], y[idx]
            pool, test = self._chronological(n)
            policy = "learning_curve"
            if len(pool) < self.min_train:
                warnings.warn(f"{dataset.code} {subject}/{session}: {n} trials, too few for a learning curve")
                continue
            if not self._usable(y_s, pool, test):
                if self.fallback is None:
                    warnings.warn(f"{dataset.code} {subject}/{session}: block-ordered cues, skipped")
                    continue
                warnings.warn(f"{dataset.code} {subject}/{session}: block-ordered cues, using a stratified "
                              "shuffled test block and class-interleaved training order")
                pool, test = self._stratified(y_s)
                policy = "learning_curve_stratified"
            for frac in self.fractions:
                train = pool[: self._n_train(len(pool), frac)]
                if not self.is_regression and len(np.unique(y_s[train])) < 2:
                    warnings.warn(f"{dataset.code} {subject}/{session} fraction {frac}: single class, skipped")
                    continue
                for name, pipeline in pipelines.items():
                    out = self._score_pipeline(pipeline, X_s[train], y_s[train], X_s[test], y_s[test],
                                               where=f"({name}, {dataset.code} {subject}/{session} fraction {frac})")
                    if out is None:
                        continue
                    for metric, score in out["scores"].items():
                        results.append({
                            "dataset": dataset.code, "subject": subject, "session": session, "pipeline": name,
                            "metric": metric, "score": score, "fold": 0, "fold_policy": policy,
                            "train_fraction": frac, "n_train": len(train), "n_test": len(test),
                            "n_channels": X_s.shape[1], "time": out["time"],
                        })
        return results
