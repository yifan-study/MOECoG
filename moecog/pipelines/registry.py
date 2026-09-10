"""Pipelines described as YAML files, the MOABB convention.

A file names the pipeline, the paradigms it applies to, its citations, and an ordered list of steps::

    name: LogBandPower + LDA
    paradigms: [EpochedClassification, MotorClassification]
    citations: [https://doi.org/10.1088/1741-2552/aadea0]
    pipeline:
      - name: LogBandPower
        from: moecog.pipelines.features
        parameters: {sfreq: 1000}
      - name: StandardScaler
        from: sklearn.preprocessing
      - name: LinearDiscriminantAnalysis
        from: sklearn.discriminant_analysis
        parameters: {solver: lsqr, shrinkage: auto}

``load_pipelines`` turns a directory (or one file) of such descriptions into ``{name: sklearn.Pipeline}``.
Parameters whose value is the string ``"$sfreq"`` are filled from the ``sfreq`` argument, so one YAML serves
datasets with different sampling rates.
"""

from __future__ import annotations

import importlib
from pathlib import Path

from sklearn.pipeline import Pipeline


def _build_step(step: dict, sfreq: float | None):
    module = importlib.import_module(step["from"])
    cls = getattr(module, step["name"])
    params = dict(step.get("parameters") or {})
    for key, value in list(params.items()):
        if value == "$sfreq":
            if sfreq is None:
                raise ValueError(f"{step['name']} needs sfreq; pass sfreq= to load_pipelines")
            params[key] = float(sfreq)
    return cls(**params)


def load_pipeline_file(path, sfreq: float | None = None):
    """Return ``(name, Pipeline, description)`` for one YAML file."""
    import yaml

    path = Path(path)
    desc = yaml.safe_load(path.read_text())
    if not isinstance(desc, dict) or "pipeline" not in desc:
        raise ValueError(f"{path}: expected a mapping with a 'pipeline' list")
    steps = [(f"{i}_{s['name']}", _build_step(s, sfreq)) for i, s in enumerate(desc["pipeline"])]
    name = desc.get("name") or path.stem
    return name, Pipeline(steps), desc


CONFIG_DIR = Path(__file__).resolve().parent / "configs"


def load_pipelines(path=None, sfreq: float | None = None, paradigm: str | None = None):
    """Build every pipeline described under ``path`` (a directory or one file).

    Parameters
    ----------
    path : str or Path or None
        Directory of ``*.yml`` / ``*.yaml`` files, or one file. None means the reference pipelines shipped
        inside the package (``moecog/pipelines/configs``).
    sfreq : float or None
        Fills ``"$sfreq"`` placeholders (feature extractors need the sampling rate).
    paradigm : str or None
        Keep only pipelines whose ``paradigms`` list contains this class name.

    Returns
    -------
    dict of str to sklearn.pipeline.Pipeline
    """
    path = CONFIG_DIR if path is None else Path(path)
    files = sorted(path.glob("*.y*ml")) if path.is_dir() else [path]
    out = {}
    for f in files:
        name, pipe, desc = load_pipeline_file(f, sfreq=sfreq)
        if paradigm and desc.get("paradigms") and paradigm not in desc["paradigms"]:
            continue
        out[name] = pipe
    return out


def describe_pipelines(path=None):
    """Return the YAML descriptions (name, paradigms, citations, steps) without building them."""
    import yaml

    path = CONFIG_DIR if path is None else Path(path)
    files = sorted(path.glob("*.y*ml")) if path.is_dir() else [path]
    return [dict(file=str(f), **yaml.safe_load(f.read_text())) for f in files]
