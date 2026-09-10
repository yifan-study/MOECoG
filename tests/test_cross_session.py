"""Leave-one-session-out evaluation on synthetic multi-session data."""

import warnings

import pytest

from moecog.datasets import FakeECoGDataset
from moecog.evaluations import CrossSessionEvaluation
from moecog.paradigms import EpochedClassification
from moecog.pipelines import classification_baselines


def test_cross_session_holds_out_every_session():
    ds = FakeECoGDataset(n_subjects=2, n_sessions=3, n_channels=6, sfreq=200.0, n_trials_per_class=8, seed=1)
    par = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=90.0)
    ev = CrossSessionEvaluation(par, [ds])
    pipes = {k: v for k, v in classification_baselines(200.0).items() if k == "LogBandPower+LDA"}
    df = ev.process(pipes)
    assert (df["fold_policy"] == "leave_one_session_out").all()
    per_subject = df[df.metric == "kappa"].groupby("subject")["session"].nunique()
    assert (per_subject == 3).all()
    assert df["n_train"].min() > df["n_test"].max()


def test_cross_session_reports_incompatible_datasets():
    single = FakeECoGDataset(n_subjects=1, n_sessions=1, n_channels=4, sfreq=200.0, n_trials_per_class=6, seed=2)
    par = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=90.0)
    with pytest.raises(ValueError, match="cross-session needs 2"):
        CrossSessionEvaluation(par, [single])
    multi = FakeECoGDataset(n_subjects=1, n_sessions=2, n_channels=4, sfreq=200.0, n_trials_per_class=6, seed=3)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ev = CrossSessionEvaluation(par, [single, multi])
    assert list(ev.skipped) == [single.code] and any("cross-session" in str(x.message) for x in w)
