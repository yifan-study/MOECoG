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
