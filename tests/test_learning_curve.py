"""Learning-curve evaluation on synthetic data: fixed final test block, growing chronological prefixes."""

from moecog.datasets import FakeECoGDataset
from moecog.evaluations import LearningCurveEvaluation
from moecog.paradigms import EpochedClassification
from moecog.pipelines import classification_baselines


def test_learning_curve_points_and_monotone_train_sizes():
    ds = FakeECoGDataset(n_subjects=1, n_sessions=1, n_channels=6, sfreq=200.0, n_trials_per_class=20, seed=5)
    par = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=90.0)
    ev = LearningCurveEvaluation(par, [ds], fractions=(0.25, 0.5, 1.0), test_fraction=0.2)
    pipes = {k: v for k, v in classification_baselines(200.0).items() if k == "LogBandPower+LDA"}
    df = ev.process(pipes)
    k = df[df.metric == "kappa"].sort_values("train_fraction")
    assert list(k["train_fraction"]) == [0.25, 0.5, 1.0]
    assert k["n_train"].is_monotonic_increasing and k["n_test"].nunique() == 1
    assert (df["fold_policy"] == "learning_curve").all()


def test_failing_pipeline_does_not_sink_the_others():
    import warnings

    from sklearn.base import BaseEstimator, ClassifierMixin

    class Broken(BaseEstimator, ClassifierMixin):
        def fit(self, X, y):
            raise RuntimeError("boom")

        def predict(self, X):
            return X[:, 0]

    ds = FakeECoGDataset(n_subjects=1, n_sessions=1, n_channels=4, sfreq=200.0, n_trials_per_class=10, seed=1)
    par = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=90.0)
    pipes = {k: v for k, v in classification_baselines(200.0).items() if k == "LogBandPower+LDA"}
    pipes["Broken"] = Broken()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        df = LearningCurveEvaluation(par, [ds], fractions=(1.0,)).process(pipes)
    assert set(df["pipeline"]) == {"LogBandPower+LDA"}
    assert any("pipeline failed (Broken" in str(x.message) for x in w)
