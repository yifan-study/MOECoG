"""One-call benchmark: datasets x paradigm x pipelines with within-subject evaluation, results to CSV.

    from moecog import benchmark
    from moecog.datasets import MillerLibrary
    from moecog.paradigms import MotorClassification

    df = benchmark([MillerLibrary("motor_basic")], MotorClassification(), pipelines="pipelines",
                   out="results/motor_basic_motor.csv")

``pipelines`` may be a directory or file of YAML descriptions (see :mod:`moecog.pipelines.registry`), a dict of
named scikit-learn estimators, or None for the package baselines matching the paradigm.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import __version__


def _default_pipelines(paradigm, sfreq):
    from .paradigms import BaseRegressionParadigm
    from .pipelines import classification_baselines, regression_baselines

    if isinstance(paradigm, BaseRegressionParadigm):
        return regression_baselines(sfreq)
    return classification_baselines(sfreq)


def benchmark(datasets, paradigm, pipelines=None, n_splits=5, subjects=None, shuffle=False, random_state=42,
              out=None, sfreq=None, overwrite=True):
    """Evaluate pipelines on datasets under one paradigm and return the per-fold results.

    Parameters
    ----------
    datasets : dataset or list of datasets
        MOECoG dataset objects (or catalog entry ids, resolved through ``moecog.catalog.ENTRIES``).
    paradigm : BaseParadigm
        Classification or regression paradigm.
    pipelines : str, Path, dict or None
        YAML directory/file, ``{name: estimator}``, or None for the built-in baselines.
    n_splits, subjects, shuffle, random_state
        Passed to :class:`moecog.evaluations.WithinSubjectCV`.
    out : str or Path or None
        CSV to write (appended to unless ``overwrite``); a ``moecog_version`` column is added.
    sfreq : float or None
        Sampling rate used to instantiate feature extractors; defaults to the paradigm's ``resample`` or the
        first dataset's ``sfreq``.

    Returns
    -------
    pandas.DataFrame
        One row per (dataset, subject, session, pipeline, fold) with the metrics of the paradigm.
    """
    from .evaluations import WithinSubjectCV

    if not isinstance(datasets, (list, tuple)):
        datasets = [datasets]
    resolved = []
    for d in datasets:
        if isinstance(d, str):
            from .catalog import ENTRIES

            resolved.append(ENTRIES[d].build())
        else:
            resolved.append(d)
    if sfreq is None:
        sfreq = getattr(paradigm, "resample", None) or getattr(resolved[0], "sfreq", None) or 1000.0
    if pipelines is None:
        pipes = _default_pipelines(paradigm, sfreq)
    elif isinstance(pipelines, dict):
        pipes = pipelines
    else:
        from .pipelines import load_pipelines

        pipes = load_pipelines(pipelines, sfreq=sfreq, paradigm=type(paradigm).__name__)
        if not pipes:
            raise ValueError(f"no pipeline in {pipelines} lists paradigm {type(paradigm).__name__}")
    ev = WithinSubjectCV(paradigm, resolved, n_splits=n_splits, shuffle=shuffle, random_state=random_state)
    df = ev.process(pipes, subjects=subjects)
    df["moecog_version"] = __version__
    if out:
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.is_file() and not overwrite:
            df = pd.concat([pd.read_csv(out), df], ignore_index=True)
        df.to_csv(out, index=False)
    return df
