"""Base evaluation class."""

from __future__ import annotations

import time
import warnings
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

    #: Load and evaluate one subject at a time. ECoG grids are patient-specific,
    #: so subjects cannot be pooled into one array; cross-subject evaluations
    #: set this to False and align channels themselves.
    per_subject = True

    def __init__(self, paradigm, datasets, n_splits=5, random_state=42):
        self.paradigm = paradigm
        self.n_splits = n_splits
        self.random_state = random_state
        self.skipped = {}  # dataset code -> reason, for datasets this evaluation cannot use
        kept = []
        for d in datasets:
            reason = self.incompatibility_reason(d)
            if reason:
                self.skipped[d.code] = reason
                warnings.warn(f"{type(self).__name__} skips {d.code}: {reason}")
            else:
                kept.append(d)
        self.datasets = kept
        if not self.datasets:
            raise ValueError("None of the datasets is valid for this evaluation: " + "; ".join(self.skipped.values()))

    def incompatibility_reason(self, dataset):
        """Why ``dataset`` cannot be used here, or None. Subclasses add their own conditions."""
        if not self.paradigm.is_valid(dataset):
            return (f"{dataset.code}: paradigm {type(self.paradigm).__name__} does not apply "
                    f"(dataset paradigm '{getattr(dataset, 'paradigm', None)}')")
        return None

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
            subs = dataset.subject_list
            if subjects is not None:
                subs = [s for s in subjects if s in dataset.subject_list]
                if not subs:
                    continue
            groups = [[s] for s in subs] if self.per_subject else [subs]
            for group in groups:
                X, y, metadata = self.paradigm.get_data(dataset, subjects=group)
                all_results.extend(self._evaluate(dataset, X, y, metadata, pipelines))
        return pd.DataFrame(all_results)

    @abstractmethod
    def _evaluate(self, dataset, X, y, metadata, pipelines):
        """Implement the cross-validation strategy; return a list of row dicts."""

    def _score_pipeline(self, pipeline, X_train, y_train, X_test, y_test, where=""):
        """Fit a clone of ``pipeline`` and compute the paradigm's metrics.

        Returns ``None`` (with a warning naming ``where``) when the pipeline raises, so one broken pipeline
        does not cost the patient's rows for the others; the missing rows stay "not yet computed" in the
        results store and are retried on the next run.
        """
        t0 = time.time()
        clf = clone(pipeline)
        try:
            try:
                clf.fit(X_train, y_train)
                y_pred = clf.predict(X_test)
            except ValueError:
                if X_train.ndim != 3:
                    raise
                clf = clone(pipeline)
                clf.fit(X_train.reshape(len(X_train), -1), y_train)
                y_pred = clf.predict(X_test.reshape(len(X_test), -1))
        except Exception as err:  # noqa: BLE001 - any estimator error is a per-pipeline failure
            warnings.warn(f"pipeline failed {where}: {type(err).__name__}: {err}")
            return None
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
