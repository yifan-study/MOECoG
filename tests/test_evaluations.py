import numpy as np
import pytest
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from moecog.evaluations import WithinSubjectCV, compute_metric, contiguous_folds
from moecog.paradigms import FingerFlexionRegression, MotorClassification
from moecog.pipelines import classification_baselines, regression_baselines
from moecog.pipelines.features import LogBandPower


def test_contiguous_folds_cover_everything():
    n = 23
    seen = []
    for train, test in contiguous_folds(n, 4):
        assert len(np.intersect1d(train, test)) == 0
        assert np.array_equal(test, np.arange(test.min(), test.max() + 1))
        seen.extend(test.tolist())
    assert sorted(seen) == list(range(n))


def test_classification_cv_beats_chance(fake_cls):
    paradigm = MotorClassification(fmin=1.0, fmax=100.0, tmax=1.0)
    ev = WithinSubjectCV(paradigm, [fake_cls], n_splits=4)
    pipes = {"lbp+lda": make_pipeline(LogBandPower(sfreq=250.0), StandardScaler(),
                                      LinearDiscriminantAnalysis())}
    res = ev.process(pipes)
    assert set(res["metric"]) == {"accuracy", "balanced_accuracy", "kappa"}
    assert set(res["fold_policy"]) == {"chronological"}
    assert paradigm.headline_metric == "kappa" and paradigm.scoring()[0] == "kappa"
    assert set(res["subject"]) == {1, 2}
    acc = res[res["metric"] == "accuracy"].groupby("subject")["score"].mean()
    assert (acc > 0.8).all(), acc


def test_classification_cv_shuffled(fake_cls):
    paradigm = MotorClassification(fmin=1.0, fmax=100.0, tmax=1.0)
    ev = WithinSubjectCV(paradigm, [fake_cls], n_splits=3, shuffle=True)
    res = ev.process(classification_baselines(sfreq=250.0), subjects=[1])
    assert res["fold"].nunique() == 3
    assert res["pipeline"].nunique() == 3


def test_regression_cv_with_purge(fake_reg):
    paradigm = FingerFlexionRegression(fmin=1.0, fmax=100.0, window_size=0.4, window_stride=0.1)
    ev = WithinSubjectCV(paradigm, [fake_reg], n_splits=4)
    assert ev._purge() == 3
    pipes = {"hg+ridge": make_pipeline(LogBandPower(bands={"hg": (60.0, 90.0)}, sfreq=250.0),
                                       StandardScaler(), Ridge(alpha=1.0))}
    res = ev.process(pipes)
    r = res[res["metric"] == "pearson_r"]["score"].mean()
    assert r > 0.5, r
    # purge removed training windows adjacent to the test block
    n_win = res["n_train"].iloc[0] + res["n_test"].iloc[0]
    assert res["n_train"].iloc[0] < n_win


def test_regression_baselines_run(fake_reg):
    paradigm = FingerFlexionRegression(fmin=1.0, fmax=100.0)
    ev = WithinSubjectCV(paradigm, [fake_reg], n_splits=3)
    res = ev.process(regression_baselines(sfreq=250.0))
    assert len(res) == 3 * 2 * 2


def test_invalid_dataset_rejected(fake_cls):
    with pytest.raises(ValueError):
        WithinSubjectCV(FingerFlexionRegression(), [fake_cls])


def test_compute_metric():
    y = np.array([0, 1, 1, 0])
    assert compute_metric("accuracy", y, y) == 1.0
    assert compute_metric("kappa", y, y) == 1.0
    assert np.isnan(compute_metric("pearson_r", np.ones(5), np.arange(5)))
    with pytest.raises(ValueError):
        compute_metric("f1", y, y)


def test_per_subject_channel_counts():
    """Patient-specific grids: subjects are never pooled into one array."""
    from moecog.datasets import FakeECoGDataset

    ds = FakeECoGDataset(n_subjects=2, n_channels={1: 6, 2: 9}, sfreq=250.0,
                         n_trials_per_class=8, isi=0.5, seed=4)
    paradigm = MotorClassification(fmin=1.0, fmax=100.0, tmax=1.0)
    with pytest.raises(ValueError, match="different channel counts"):
        paradigm.get_data(ds)
    res = WithinSubjectCV(paradigm, [ds], n_splits=2).process(
        {"lbp+lda": make_pipeline(LogBandPower(sfreq=250.0), LinearDiscriminantAnalysis())})
    assert set(res.groupby("subject")["n_channels"].first()) == {6, 9}


def test_blocked_cues_fall_back_to_stratified():
    from moecog.datasets import FakeECoGDataset

    blocked = FakeECoGDataset(n_subjects=1, n_channels=6, sfreq=250.0, n_trials_per_class=10,
                              isi=0.5, seed=6, cue_order="blocked")
    paradigm = MotorClassification(fmin=1.0, fmax=100.0, tmax=1.0)
    pipes = {"lbp+lda": make_pipeline(LogBandPower(sfreq=250.0), LinearDiscriminantAnalysis())}
    with pytest.warns(UserWarning, match="block-ordered"):
        res = WithinSubjectCV(paradigm, [blocked], n_splits=5).process(pipes)
    assert set(res["fold_policy"]) == {"stratified_fallback"}
    assert res[res["metric"] == "kappa"]["score"].notna().all()
    strict = WithinSubjectCV(paradigm, [blocked], n_splits=5, fallback=None)
    with pytest.warns(UserWarning):
        res2 = strict.process(pipes)
    assert set(res2["fold_policy"]) == {"chronological"}
    with pytest.raises(ValueError):
        WithinSubjectCV(paradigm, [blocked], fallback="random")
