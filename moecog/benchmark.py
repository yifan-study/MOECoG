"""One-call benchmark: datasets x paradigm x pipelines under one or more evaluations, results appended to a store.

    from moecog import benchmark
    from moecog.datasets import MillerLibrary
    from moecog.paradigms import MotorClassification

    df = benchmark([MillerLibrary("motor_basic")], MotorClassification(), out="results/motor_basic_motor.csv")

``datasets`` may hold dataset objects or catalog entry ids; ``paradigm`` a paradigm object or a class name
resolved with parameters from a context YAML (``moecog/paradigms/contexts/*.yml`` or your own);
``pipelines`` a YAML directory/file, a dict of estimators, or None for the reference pipelines shipped in the
package. Rows already present in ``out`` (same dataset, subject, pipeline parameters, paradigm parameters and
evaluation) are skipped unless ``overwrite=True``, and every (dataset, pipeline) pair that cannot run is
reported with its reason instead of being dropped silently.
"""

from __future__ import annotations

import warnings
from pathlib import Path

from .alignment import ALIGNMENTS

EVALUATIONS = {"within_subject": "WithinSubjectCV", "cross_session": "CrossSessionEvaluation",
               "learning_curve": "LearningCurveEvaluation"}


def _resolve_paradigm(paradigm, contexts):
    if not isinstance(paradigm, str):
        return paradigm
    import moecog.paradigms as P

    cls = getattr(P, paradigm)
    kwargs = {}
    if contexts:
        if isinstance(contexts, dict):
            kwargs = dict(contexts.get(paradigm, contexts))
        else:
            import yaml

            kwargs = dict((yaml.safe_load(Path(contexts).read_text()) or {}).get(paradigm, {}))
    return cls(**kwargs)


def _default_pipelines(paradigm, sfreq):
    """The shipped YAML pipelines for this paradigm that need no optional dependency.

    One registry, one set of names: what ``benchmark()`` runs by default is exactly what the leaderboard and the
    reference runs call ``LogBandPower + LDA`` and friends; pipelines with a ``requires:`` line (pyriemann,
    braindecode) are opt-in through ``pipelines=``.
    """
    from .pipelines import describe_pipelines, load_pipelines

    optional = {d["name"] for d in describe_pipelines() if d.get("requires")}
    pipes = load_pipelines(sfreq=sfreq, paradigm=type(paradigm).__name__)
    return {name: p for name, p in pipes.items() if name not in optional}


def benchmark(datasets, paradigm, pipelines=None, evaluations=("within_subject",), n_splits=5, subjects=None,
              shuffle=False, random_state=42, out=None, sfreq=None, overwrite=False, contexts=None,
              verbose=True):
    """Evaluate pipelines on datasets and return every stored row (see the module docstring).

    Parameters
    ----------
    datasets : dataset, catalog id, or list of them
    paradigm : BaseParadigm or str
        Object, or class name from :mod:`moecog.paradigms` instantiated with ``contexts``.
    pipelines : str, Path, dict or None
    evaluations : sequence of {"within_subject", "cross_session", "learning_curve"}, each optionally suffixed
        ``":ea"``, ``":recenter"`` or ``":zscore"`` for label-free per-session alignment (``"cross_session:ea"``);
        the full string is the ``evaluation`` label of the rows
    n_splits, subjects, shuffle, random_state
        Passed to the within-subject evaluation.
    out : str or Path or None
        Results CSV (a :class:`moecog.analysis.ResultsStore`); None keeps results in memory only.
    sfreq : float or None
        Sampling rate for feature extractors; defaults to the paradigm's ``resample`` or the first dataset's.
    overwrite : bool
        Recompute the requested rows and replace them in ``out`` (other rows stay); use a new ``out`` path for
        a fresh file.
    contexts : dict, str or Path or None
        Paradigm parameters keyed by class name (used when ``paradigm`` is a name).

    Returns
    -------
    pandas.DataFrame
        All rows in the store after this run (including earlier runs when ``out`` existed).
    """
    import tempfile

    from . import evaluations as E
    from .analysis import ResultsStore

    if not isinstance(datasets, (list, tuple)):
        datasets = [datasets]
    resolved = []
    for d in datasets:
        if isinstance(d, str):
            from .catalog import ENTRIES

            resolved.append(ENTRIES[d].build())
        else:
            resolved.append(d)
    paradigm = _resolve_paradigm(paradigm, contexts)
    if sfreq is None:
        sfreq = getattr(paradigm, "resample", None) or getattr(resolved[0], "sfreq", None) or 1000.0
        if not sfreq or sfreq != sfreq:  # NaN
            sfreq = 1000.0
    if pipelines is None:
        pipes = _default_pipelines(paradigm, sfreq)
    elif isinstance(pipelines, dict):
        pipes = pipelines
    else:
        from .pipelines import load_pipelines

        pipes = load_pipelines(pipelines, sfreq=sfreq, paradigm=type(paradigm).__name__)
        if not pipes:
            raise ValueError(f"no pipeline in {pipelines} lists paradigm {type(paradigm).__name__}")
    store = ResultsStore(out if out else Path(tempfile.mkdtemp()) / "results.csv")
    skipped = []
    for ev_name in evaluations:
        base_name, _, alignment = ev_name.partition(":")
        if base_name not in EVALUATIONS:
            raise ValueError(f"unknown evaluation {ev_name!r}; choose from {sorted(EVALUATIONS)}, optionally "
                             "suffixed ':ea', ':recenter' or ':zscore' for per-session alignment")
        if alignment and alignment not in ALIGNMENTS:
            raise ValueError(f"unknown alignment {alignment!r} in {ev_name!r}; choose from {sorted(ALIGNMENTS)}")
        cls = getattr(E, EVALUATIONS[base_name])
        kwargs = dict(random_state=random_state, alignment=alignment or None)
        if base_name == "within_subject":
            kwargs.update(n_splits=n_splits, shuffle=shuffle)
        try:
            ev = cls(paradigm, resolved, **kwargs)
        except ValueError as err:
            skipped.append((ev_name, "*", str(err)))
            continue
        for code, reason in ev.skipped.items():
            skipped.append((ev_name, code, reason))
        for ds in ev.datasets:
            others = store.paradigm_mismatch(ds.code, ev_name, paradigm)
            if others:
                warnings.warn(f"{ds.code} {ev_name}: the store already holds rows computed under another paradigm "
                              f"(digest(s) {', '.join(others)}, e.g. a different sampling rate); tables grouped by "
                              "pipeline name would mix protocols. Pass the same paradigm or a fresh --out.")
            subs = ds.subject_list if subjects is None else [s for s in subjects if s in ds.subject_list]
            for subject in subs:
                todo = pipes if overwrite else store.not_yet_computed(pipes, ds.code, subject, paradigm, ev_name)
                if not todo:
                    continue
                try:
                    rows = ev.process(todo, subjects=[subject])
                except Exception as err:  # noqa: BLE001
                    skipped.append((ev_name, f"{ds.code}/{subject}", f"{type(err).__name__}: {err}"))
                    continue
                store.add(rows, todo, paradigm, ev_name, replace=overwrite)
    if verbose and skipped:
        for ev_name, where, reason in skipped:
            print(f"[skipped] {ev_name} {where}: {reason}")
    df = store.to_dataframe()
    df.attrs["skipped"] = skipped
    return df
