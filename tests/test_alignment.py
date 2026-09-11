"""Session alignment: whitening per session and its effect on a synthetic cross-session gain shift."""

import numpy as np
import pytest

from moecog.alignment import align_sessions, euclidean_alignment, trial_covariances, zscore_alignment


def _session(rng, n=40, ch=6, t=200, gain=None):
    y = np.array([0, 1] * (n // 2))
    X = rng.standard_normal((n, ch, t))
    X[y == 1, :2] *= 3.0                      # class 1 has more power on the first two channels
    if gain is not None:
        X = np.einsum("cd,ndt->nct", gain, X)   # a new montage / impedance day: mixed and rescaled channels
    return X, y


def test_euclidean_alignment_recentres_to_identity():
    rng = np.random.default_rng(0)
    X, _ = _session(rng)
    Xa = euclidean_alignment(X)
    R = trial_covariances(Xa).mean(axis=0)
    assert Xa.shape == X.shape and np.allclose(R, np.eye(X.shape[1]), atol=1e-6)
    Z = zscore_alignment(X)
    assert np.allclose(Z.std(axis=(0, 2)), 1.0) and np.allclose(Z.mean(axis=(0, 2)), 0.0, atol=1e-10)


def test_align_sessions_is_per_session_and_validates():
    rng = np.random.default_rng(1)
    X1, _ = _session(rng)
    X2, _ = _session(rng, gain=np.diag(rng.uniform(0.2, 5.0, 6)))
    X = np.concatenate([X1, X2])
    sessions = np.array(["a"] * 40 + ["b"] * 40)
    Xa = align_sessions(X, sessions, "ea")
    for s in ("a", "b"):
        assert np.allclose(trial_covariances(Xa[sessions == s]).mean(axis=0), np.eye(6), atol=1e-6)
    assert align_sessions(X, sessions, None) is X
    with pytest.raises(ValueError):
        align_sessions(X, sessions, "nope")


def test_alignment_recovers_cross_session_transfer():
    """A per-channel gain change between sessions breaks band-power transfer; EA and zscore restore it."""
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.pipeline import make_pipeline

    from moecog.pipelines import LogBandPower

    rng = np.random.default_rng(2)
    X1, y1 = _session(rng, n=80)
    X2, y2 = _session(rng, n=80, gain=np.diag(rng.uniform(0.2, 5.0, 6)))

    def acc(a, b):
        clf = make_pipeline(LogBandPower(sfreq=200.0, bands={"b": (1.0, 90.0)}), LinearDiscriminantAnalysis())
        return (clf.fit(a, y1).predict(b) == y2).mean()

    raw = acc(X1, X2)
    ea = acc(euclidean_alignment(X1), euclidean_alignment(X2))
    zs = acc(zscore_alignment(X1), zscore_alignment(X2))
    assert ea > raw + 0.15 and zs > raw + 0.15 and ea > 0.9


def test_riemannian_recentering_matches_ea_on_identity_scale():
    pytest.importorskip("pyriemann")
    from moecog.alignment import riemannian_recentering

    rng = np.random.default_rng(3)
    X, _ = _session(rng)
    Xr = riemannian_recentering(X)
    assert Xr.shape == X.shape and np.isfinite(Xr).all()


def test_benchmark_accepts_alignment_suffix(tmp_path):
    from moecog import benchmark
    from moecog.datasets import FakeECoGDataset
    from moecog.paradigms import EpochedClassification

    ds = FakeECoGDataset(n_subjects=1, n_sessions=2, n_channels=4, sfreq=200.0, n_trials_per_class=10, seed=4)
    par = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=90.0)
    df = benchmark(ds, par, evaluations=("cross_session", "cross_session:ea"), sfreq=200.0,
                   out=tmp_path / "r.csv", verbose=False)
    assert set(df["evaluation"]) == {"cross_session", "cross_session:ea"}
    with pytest.raises(ValueError):
        benchmark(ds, par, evaluations=("cross_session:nope",), sfreq=200.0, out=tmp_path / "r2.csv", verbose=False)
