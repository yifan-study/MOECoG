"""Base evaluation class."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from sklearn.base import clone


class BaseEvaluation(ABC):
    """Base class for all evaluation strategies.

    Parameters
    ----------
    paradigm : BaseParadigm
        Paradigm instance defining the task.
    datasets : list of BaseECoGDataset
        Datasets to evaluate on (filtered for paradigm compatibility).
    n_splits : int
        Number of cross-validation folds.
    random_state : int
        Random seed for reproducibility.
    """

    def __init__(self, paradigm, datasets, n_splits=5, random_state=42):
        self.paradigm = paradigm
        self.datasets = [d for d in datasets if paradigm.is_valid(d)]
        if not self.datasets:
            raise ValueError("None of the datasets is valid for this paradigm")
        self.n_splits = n_splits
        self.random_state = random_state

    def process(self, pipelines, subjects=None):
        """Run all pipelines on all compatible datasets.

        Parameters
        ----------
        pipelines : dict of str to sklearn estimator
            Named pipelines to evaluate.
        subjects : list or None
            Restrict to these subjects (applied to every dataset that has them).

        Returns
        -------
        pd.DataFrame
            One row per (dataset, subject, session, pipeline, metric, fold).
        """
        all_results = []
        for dataset in self.datasets:
            subs = None
            if subjects is not None:
                subs = [s for s in subjects if s in dataset.subject_list]
                if not subs:
                    continue
            X, y, metadata = self.paradigm.get_data(dataset, subjects=subs)
            all_results.extend(self._evaluate(dataset, X, y, metadata, pipelines))
        return pd.DataFrame(all_results)

    @abstractmethod
    def _evaluate(self, dataset, X, y, metadata, pipelines):
        """Implement the cross-validation strategy; return a list of row dicts."""

    def _score_pipeline(self, pipeline, X_train, y_train, X_test, y_test):
        """Fit a clone of ``pipeline`` and compute the paradigm's metrics."""
        t0 = time.time()
        clf = clone(pipeline)
        try:
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
        except ValueError:
            if X_train.ndim != 3:
                raise
            clf = clone(pipeline)
            clf.fit(X_train.reshape(len(X_train), -1), y_train)
            y_pred = clf.predict(X_test.reshape(len(X_test), -1))
        duration = time.time() - t0

        scoring = self.paradigm.scoring()
        names = [scoring] if isinstance(scoring, str) else list(scoring)
        scores = {name: compute_metric(name, y_test, y_pred) for name in names}
        return {"scores": scores, "time": duration}


def compute_metric(metric_name, y_true, y_pred):
    """Compute one evaluation metric.

    Supported: ``pearson_r`` (mean over targets), ``r2``, ``accuracy``,
    ``balanced_accuracy``, ``kappa``.
    """
    from scipy.stats import pearsonr
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        cohen_kappa_score,
        r2_score,
    )

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if metric_name == "pearson_r":
        if y_true.ndim == 1:
            y_true, y_pred = y_true[:, None], y_pred[:, None]
        rs = []
        for i in range(y_true.shape[1]):
            if np.std(y_true[:, i]) == 0 or np.std(y_pred[:, i]) == 0:
                rs.append(np.nan)
            else:
                rs.append(pearsonr(y_true[:, i], y_pred[:, i])[0])
        return float(np.nanmean(rs))
    if metric_name == "r2":
        return float(r2_score(y_true, y_pred, multioutput="uniform_average"))
    if metric_name == "accuracy":
        return float(accuracy_score(y_true, y_pred))
    if metric_name == "balanced_accuracy":
        return float(balanced_accuracy_score(y_true, y_pred))
    if metric_name == "kappa":
        return float(cohen_kappa_score(y_true, y_pred))
    raise ValueError(f"Unknown metric: {metric_name}")


# backwards-compatible private alias
_compute_metric = compute_metric
