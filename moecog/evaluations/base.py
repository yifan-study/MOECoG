"""Base evaluation class."""

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
        self.n_splits = n_splits
        self.random_state = random_state

    def process(self, pipelines):
        """Run all pipelines on all compatible datasets.

        Parameters
        ----------
        pipelines : dict of str to sklearn estimator
            Named pipelines to evaluate.

        Returns
        -------
        pd.DataFrame
            Results with columns: dataset, subject, session, pipeline,
            score, metric, time, n_samples, n_channels, fold.
        """
        all_results = []
        for dataset in self.datasets:
            X, y, metadata = self.paradigm.get_data(dataset)
            results = self._evaluate(dataset, X, y, metadata, pipelines)
            all_results.extend(results)
        return pd.DataFrame(all_results)

    @abstractmethod
    def _evaluate(self, dataset, X, y, metadata, pipelines):
        """Implement the cross-validation strategy.

        Returns
        -------
        list of dict
            One dict per (pipeline, fold, subject) combination.
        """

    def _score_pipeline(self, pipeline, X_train, y_train, X_test, y_test):
        """Fit a pipeline and compute scores."""
        t0 = time.time()
        clf = clone(pipeline)

        if X_train.ndim == 3:
            try:
                clf.fit(X_train, y_train)
                y_pred = clf.predict(X_test)
            except ValueError:
                X_tr = X_train.reshape(X_train.shape[0], -1)
                X_te = X_test.reshape(X_test.shape[0], -1)
                clf.fit(X_tr, y_train)
                y_pred = clf.predict(X_te)
        else:
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)

        duration = time.time() - t0

        scoring = self.paradigm.scoring()
        if isinstance(scoring, str):
            scores = {scoring: _compute_metric(scoring, y_test, y_pred)}
        else:
            scores = {
                name: _compute_metric(name, y_test, y_pred) for name in scoring
            }

        return {"scores": scores, "time": duration}


def _compute_metric(metric_name, y_true, y_pred):
    """Compute a single evaluation metric."""
    from scipy.stats import pearsonr
    from sklearn.metrics import accuracy_score, cohen_kappa_score, r2_score

    if metric_name == "pearson_r":
        if y_true.ndim == 1:
            return pearsonr(y_true, y_pred)[0]
        rs = [pearsonr(y_true[:, i], y_pred[:, i])[0] for i in range(y_true.shape[1])]
        return float(np.mean(rs))
    elif metric_name == "r2":
        return r2_score(y_true, y_pred, multioutput="uniform_average")
    elif metric_name == "accuracy":
        return accuracy_score(y_true, y_pred)
    elif metric_name == "kappa":
        return cohen_kappa_score(y_true, y_pred)
    else:
        raise ValueError(f"Unknown metric: {metric_name}")
