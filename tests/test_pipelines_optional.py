"""Optional pipeline families (pyriemann, braindecode) on synthetic epochs; skipped when not installed."""

import numpy as np
import pytest

from moecog.pipelines import load_pipelines


def _xy(n=24, n_ch=6, n_t=100, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, n_ch, n_t)).astype(np.float32)
    y = np.array(["a", "b"] * (n // 2))
    X[y == "b", :2] *= 3.0  # class b has more variance on the first two channels
    return X, y


def test_optional_pipelines_are_reported_not_silent():
    import warnings

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        pipes = load_pipelines(sfreq=200.0, paradigm="EpochedClassification")
    assert {"LogBandPower + LDA", "LogBandPower + LogReg", "HighGamma + LDA"} <= set(pipes)


def test_riemann_pipeline_fits():
    pytest.importorskip("pyriemann")
    pipes = load_pipelines(sfreq=200.0, paradigm="EpochedClassification")
    clf = pipes["Riemann TS + LogReg"]
    X, y = _xy()
    clf.fit(X, y)
    assert (clf.predict(X) == y).mean() > 0.7


def test_braindecode_wrapper_fits_and_predicts():
    pytest.importorskip("braindecode")
    torch = pytest.importorskip("torch")
    try:
        torch.from_numpy(np.zeros(1, np.float32))
    except RuntimeError:  # torch <= 2.2 (last build for Intel macOS) cannot read NumPy 2 arrays; skorch needs it
        pytest.skip("torch's NumPy bridge is unavailable in this environment (torch built against NumPy 1)")
    from moecog.pipelines.deep import BraindecodeClassifier

    X, y = _xy(n=32, n_ch=4, n_t=120)
    clf = BraindecodeClassifier(n_epochs=3, batch_size=8, random_state=1)
    clf.fit(X, y)
    pred = clf.predict(X)
    assert pred.shape == y.shape and set(pred) <= {"a", "b"}
    proba = clf.predict_proba(X)
    assert proba.shape == (32, 2) and np.allclose(proba.sum(axis=1), 1.0, atol=1e-4)
