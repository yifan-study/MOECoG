"""One-call benchmark and YAML pipeline registry on synthetic data."""

import pytest

from moecog import benchmark
from moecog.datasets import FakeECoGDataset
from moecog.paradigms import EpochedClassification
from moecog.pipelines import describe_pipelines, load_pipelines


def test_yaml_registry_builds_every_shipped_pipeline():
    pipes = load_pipelines(sfreq=250.0)
    names = set(pipes)
    assert {"LogBandPower + LDA", "HighGamma + Ridge"} <= names
    for p in pipes.values():
        assert hasattr(p, "fit") and len(p.steps) >= 1
    clf = load_pipelines(sfreq=250.0, paradigm="EpochedClassification")
    reg = load_pipelines(sfreq=250.0, paradigm="FingerFlexionRegression")
    assert clf and reg and not (set(clf) & set(reg))
    descs = describe_pipelines()
    assert all(d.get("citations") for d in descs)


def test_sfreq_placeholder_requires_value(tmp_path):
    (tmp_path / "p.yml").write_text(
        "name: x\npipeline:\n  - name: LogBandPower\n    from: moecog.pipelines.features\n"
        "    parameters: {sfreq: $sfreq}\n"
    )
    with pytest.raises(ValueError, match="sfreq"):
        load_pipelines(tmp_path)


def test_benchmark_one_call_and_incremental_store(tmp_path):
    ds = FakeECoGDataset(n_subjects=2, n_sessions=2, n_channels=6, sfreq=200.0, n_trials_per_class=8, seed=0)
    par = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=90.0)
    out = tmp_path / "res.csv"
    df = benchmark(ds, par, n_splits=3, out=out, sfreq=200.0, evaluations=("within_subject", "cross_session"))
    assert len(df) > 0 and out.is_file()
    expected = {"pipeline", "subject", "metric", "score", "moecog_version", "pipeline_digest", "evaluation"}
    assert expected <= set(df.columns)
    assert set(df["evaluation"]) == {"within_subject", "cross_session"}
    assert df["pipeline"].nunique() == 3  # the three classification baselines
    assert (df[df.metric == "kappa"].score.abs() <= 1).all()
    n = len(df)
    again = benchmark(ds, par, n_splits=3, out=out, sfreq=200.0, evaluations=("within_subject", "cross_session"))
    assert len(again) == n  # everything was already computed: nothing appended
    more = benchmark(ds, par, n_splits=3, out=out, sfreq=200.0, overwrite=True)
    assert len(more) == n  # within-subject rows replaced in place, cross-session rows kept
    assert (more[more.evaluation == "cross_session"]["computed_at"].to_numpy()
            == df[df.evaluation == "cross_session"]["computed_at"].to_numpy()).all()


def test_benchmark_paradigm_by_name_with_context(tmp_path):
    ds = FakeECoGDataset(n_subjects=1, n_channels=4, sfreq=200.0, n_trials_per_class=6, seed=4)
    df = benchmark(ds, "EpochedClassification", contexts={"EpochedClassification": {"tmin": 0.0, "tmax": 1.0,
                                                                                    "fmin": 1.0, "fmax": 90.0}},
                   n_splits=3, sfreq=200.0, out=tmp_path / "r.csv")
    assert len(df) > 0 and "skipped" in df.attrs


def test_results_store_merge_from_adds_only_missing_keys(tmp_path):
    import pandas as pd

    from moecog.analysis import ResultsStore

    cols = ["dataset", "subject", "session", "pipeline", "pipeline_digest", "paradigm_digest", "evaluation",
            "metric", "score", "fold"]
    a = pd.DataFrame([["D", "s1", "0", "P", "p1", "q", "within_subject", "kappa", 0.5, 0]], columns=cols)
    b = pd.DataFrame([["D", "s1", "0", "P", "p1", "q", "within_subject", "kappa", 0.9, 0],
                      ["D", "s2", "0", "P", "p1", "q", "within_subject", "kappa", 0.7, 0]], columns=cols)
    a.to_csv(tmp_path / "a.csv", index=False)
    store = ResultsStore(tmp_path / "a.csv")
    added = store.merge_from(b)
    assert list(added["subject"]) == ["s2"]
    df = ResultsStore(tmp_path / "a.csv").to_dataframe()
    assert len(df) == 2 and df[df.subject == "s1"]["score"].item() == 0.5
    store.merge_from(b, replace=True)
    df = ResultsStore(tmp_path / "a.csv").to_dataframe()
    assert len(df) == 2 and df[df.subject == "s1"]["score"].item() == 0.9


def test_results_store_reports_paradigm_mismatch(tmp_path):
    import pandas as pd

    from moecog.analysis import ResultsStore, paradigm_digest
    from moecog.paradigms import EpochedClassification

    par = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=90.0)
    other = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=90.0, resample=100.0)
    rows = pd.DataFrame([{"dataset": "D", "subject": "s1", "session": "0", "pipeline": "P", "pipeline_digest": "p",
                          "paradigm_digest": paradigm_digest(other), "evaluation": "within_subject",
                          "metric": "kappa", "score": 0.1, "fold": 0}])
    rows.to_csv(tmp_path / "r.csv", index=False)
    store = ResultsStore(tmp_path / "r.csv")
    assert store.paradigm_mismatch("D", "within_subject", par) == [paradigm_digest(other)]
    assert store.paradigm_mismatch("D", "within_subject", other) == []
    assert store.paradigm_mismatch("D", "cross_session", par) == []


def test_benchmark_defaults_are_the_registry_pipelines_without_optional_deps():
    from moecog.benchmark import _default_pipelines
    from moecog.paradigms import EpochedClassification, FingerFlexionRegression
    from moecog.pipelines import describe_pipelines

    optional = {d["name"] for d in describe_pipelines() if d.get("requires")}
    clf = _default_pipelines(EpochedClassification(), 250.0)
    reg = _default_pipelines(FingerFlexionRegression(), 250.0)
    assert {"LogBandPower + LDA", "LogBandPower + LogReg", "HighGamma + LDA"} <= set(clf)
    assert {"LogBandPower + Ridge", "HighGamma + Ridge"} <= set(reg)
    assert not (set(clf) | set(reg)) & optional
