"""Leave-one-session-out evaluation within each patient."""

from __future__ import annotations

import warnings

import numpy as np

from .base import BaseEvaluation


class CrossSessionEvaluation(BaseEvaluation):
    """Train on all but one session of a patient, test on the held-out session; every session is held out once.

    Sessions are ordered chronologically when their labels sort as numbers or ISO dates, so the fold index
    follows recording order. Patients with fewer than ``min_sessions`` sessions are skipped with a warning
    rather than silently dropped.

    Parameters
    ----------
    paradigm, datasets, random_state
        See :class:`~moecog.evaluations.base.BaseEvaluation`.
    min_sessions : int
        Minimum number of sessions a patient needs (default 2).
    """

    def __init__(self, paradigm, datasets, random_state=42, min_sessions=2):
        self.min_sessions = int(min_sessions)  # before the base class filters datasets with incompatibility_reason
        super().__init__(paradigm, datasets, n_splits=None, random_state=random_state)

    def incompatibility_reason(self, dataset):
        base = super().incompatibility_reason(dataset)
        if base:
            return base
        n = getattr(dataset, "n_sessions", None) or getattr(dataset, "sessions_per_subject", None)
        if n is not None and n < self.min_sessions:
            return f"{dataset.code}: {n} session(s) per subject, cross-session needs {self.min_sessions}"
        return None

    @staticmethod
    def _ordered(sessions):
        def key(s):
            try:
                return (0, float(s))
            except (TypeError, ValueError):
                return (1, str(s))
        return sorted(sessions, key=key)

    def _evaluate(self, dataset, X, y, metadata, pipelines):
        results = []
        is_regression = len(np.asarray(y).shape) > 1 or np.asarray(y).dtype.kind == "f"
        for subject, idx_s in metadata.groupby("subject", sort=False).indices.items():
            idx_s = np.asarray(idx_s)
            sessions = self._ordered(metadata.iloc[idx_s]["session"].unique())
            if len(sessions) < self.min_sessions:
                warnings.warn(f"{dataset.code} {subject}: {len(sessions)} session(s), cross-session skipped")
                continue
            ses_of = metadata.iloc[idx_s]["session"].to_numpy()
            for fold, held_out in enumerate(sessions):
                test = idx_s[ses_of == held_out]
                train = idx_s[ses_of != held_out]
                if not is_regression and (len(np.unique(y[train])) < 2 or len(np.unique(y[test])) < 2):
                    warnings.warn(f"{dataset.code} {subject} session {held_out}: single class in train or test")
                    continue
                for name, pipeline in pipelines.items():
                    out = self._score_pipeline(pipeline, X[train], y[train], X[test], y[test],
                                               where=f"({name}, {dataset.code} {subject} -> session {held_out})")
                    if out is None:
                        continue
                    for metric, score in out["scores"].items():
                        results.append({
                            "dataset": dataset.code, "subject": subject, "session": held_out,
                            "pipeline": name, "metric": metric, "score": score, "fold": fold,
                            "fold_policy": "leave_one_session_out", "n_train": len(train),
                            "n_test": len(test), "n_channels": X.shape[1], "time": out["time"],
                        })
        return results
