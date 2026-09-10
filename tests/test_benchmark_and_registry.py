"""One-call benchmark and YAML pipeline registry on synthetic data."""

from pathlib import Path

import pytest

from moecog import benchmark
from moecog.datasets import FakeECoGDataset
from moecog.paradigms import EpochedClassification
from moecog.pipelines import describe_pipelines, load_pipelines

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"


def test_yaml_registry_builds_every_shipped_pipeline():
    pipes = load_pipelines(PIPELINES, sfreq=250.0)
    names = set(pipes)
    assert {"LogBandPower + LDA", "HighGamma + Ridge"} <= names
    for p in pipes.values():
        assert hasattr(p, "fit") and len(p.steps) >= 2
    clf = load_pipelines(PIPELINES, sfreq=250.0, paradigm="EpochedClassification")
    reg = load_pipelines(PIPELINES, sfreq=250.0, paradigm="FingerFlexionRegression")
    assert clf and reg and not (set(clf) & set(reg))
    descs = describe_pipelines(PIPELINES)
    assert all(d.get("citations") for d in descs)


def test_sfreq_placeholder_requires_value(tmp_path):
    (tmp_path / "p.yml").write_text(
        "name: x\npipeline:\n  - name: LogBandPower\n    from: moecog.pipelines.features\n"
        "    parameters: {sfreq: $sfreq}\n"
    )
    with pytest.raises(ValueError, match="sfreq"):
        load_pipelines(tmp_path)


def test_benchmark_one_call(tmp_path):
    ds = FakeECoGDataset(n_subjects=2, n_channels=6, sfreq=200.0, n_trials_per_class=8, seed=0)
    par = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=90.0)
    out = tmp_path / "res.csv"
    df = benchmark(ds, par, pipelines=PIPELINES, n_splits=3, out=out, sfreq=200.0)
    assert len(df) > 0 and out.is_file()
    assert {"pipeline", "subject", "metric", "score", "moecog_version"} <= set(df.columns)
    assert df["pipeline"].nunique() == 3  # the three classification YAMLs
    assert (df[df.metric == "kappa"].score.abs() <= 1).all()
