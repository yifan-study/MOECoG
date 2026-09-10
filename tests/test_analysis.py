"""Results store digests, paired statistics and plots on synthetic results."""

import numpy as np
import pandas as pd
import pytest
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from moecog.analysis import (
    ResultsStore,
    compute_dataset_statistics,
    find_significant_differences,
    paired_permutation,
    paired_wilcoxon,
    paradigm_digest,
    pipeline_digest,
    rank_pipelines,
)
from moecog.paradigms import EpochedClassification


def _fake_results(n_datasets=2, n_subjects=8, n_folds=5, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(n_datasets):
        for s in range(n_subjects):
            base = rng.uniform(0.3, 0.6)
            for pipe, shift in (("A", 0.0), ("B", 0.15), ("C", -0.05)):
                for f in range(n_folds):
                    rows.append({"dataset": f"ds{d}", "subject": f"s{s}", "session": "0", "pipeline": pipe,
                                 "metric": "kappa", "score": base + shift + rng.normal(0, 0.03), "fold": f})
    return pd.DataFrame(rows)


def test_paired_tests_direction():
    a = np.array([0.6, 0.7, 0.65, 0.8, 0.72, 0.69, 0.75, 0.66])
    b = a - 0.1
    p_ab, direction = paired_wilcoxon(a, b)
    p_ba, _ = paired_wilcoxon(b, a)
    assert direction == 1 and p_ab < 0.05 < p_ba
    assert paired_permutation(a, b) < 0.05 < paired_permutation(b, a)


def test_dataset_statistics_and_combination():
    df = _fake_results()
    st = compute_dataset_statistics(df)
    assert set(st.columns) >= {"dataset", "pipe1", "pipe2", "p", "smd", "nsub", "method"}
    assert (st["method"] == "permutation").all()  # 8 patients < perm_cutoff
    P, T = find_significant_differences(df)
    assert P.loc["B", "A"] < 0.01 and P.loc["A", "B"] > 0.5
    assert T.loc["B", "A"] > 0 and T.loc["A", "B"] < 0
    ranks = rank_pipelines(df)
    assert list(ranks["pipeline"]) == ["B", "A", "C"]
    assert ranks.attrs.get("friedman_p", 1.0) < 0.01


def test_results_store_skips_computed(tmp_path):
    par = EpochedClassification(tmin=0.0, tmax=1.0)
    pipes = {"lda": make_pipeline(StandardScaler(), LinearDiscriminantAnalysis())}
    d1 = pipeline_digest(pipes["lda"])
    assert d1 == pipeline_digest(make_pipeline(StandardScaler(), LinearDiscriminantAnalysis()))
    assert d1 != pipeline_digest(make_pipeline(StandardScaler(), LinearDiscriminantAnalysis(solver="lsqr")))
    assert paradigm_digest(par) != paradigm_digest(EpochedClassification(tmin=0.0, tmax=2.0))
    store = ResultsStore(tmp_path / "r.csv")
    rows = [{"dataset": "fake", "subject": "1", "session": "0", "pipeline": "lda", "metric": "kappa",
             "score": 0.5, "fold": 0}]
    assert store.not_yet_computed(pipes, "fake", "1", par, "within_subject") == pipes
    store.add(rows, pipes, par, "within_subject")
    assert store.not_yet_computed(pipes, "fake", "1", par, "within_subject") == {}
    assert store.not_yet_computed(pipes, "fake", "2", par, "within_subject") == pipes
    again = ResultsStore(tmp_path / "r.csv")
    assert len(again.to_dataframe()) == 1 and "moecog_version" in again.to_dataframe().columns
    fresh = ResultsStore(tmp_path / "r.csv", overwrite=True)
    assert fresh.to_dataframe().empty


def test_plots_render_with_agg():
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    from moecog.analysis import paired_plot, ranking_plot, score_plot, summary_plot

    df = _fake_results()
    assert score_plot(df) is not None
    assert paired_plot(df, "B", "A") is not None
    P, T = find_significant_differences(df)
    assert summary_plot(P, T) is not None
    assert ranking_plot(df) is not None
