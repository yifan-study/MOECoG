import numpy as np
import pytest

from moecog.datasets import FakeECoGDataset
from moecog.paradigms import (
    CursorRegression,
    EpochedClassification,
    FingerFlexionRegression,
    MotorClassification,
)


def test_epoched_classification_shapes(fake_cls):
    paradigm = MotorClassification(fmin=1.0, fmax=100.0, tmax=1.0)
    assert paradigm.is_valid(fake_cls)
    X, y, meta = paradigm.get_data(fake_cls, subjects=[1])
    assert X.shape[0] == 24 and X.shape[1] == 8
    assert X.shape[2] == int(1.0 * 250) + 1
    assert set(y) == {"hand", "tongue"}
    assert list(meta.columns) == ["subject", "session", "run", "trial", "onset"]
    assert (np.diff(meta["onset"]) > 0).all()


def test_event_subset_and_validity(fake_cls):
    only_hand = EpochedClassification(events=["hand"], fmax=100.0)
    assert not only_hand.is_valid(fake_cls)
    both = EpochedClassification(events=["hand", "tongue", "missing"], fmax=100.0)
    assert both.is_valid(fake_cls)
    assert both.used_events(fake_cls) == {"hand": 1, "tongue": 2}


def test_resample(fake_cls):
    paradigm = MotorClassification(fmin=1.0, fmax=50.0, tmax=1.0, resample=125.0)
    X, _, _ = paradigm.get_data(fake_cls, subjects=[1])
    assert X.shape[2] == int(1.0 * 125) + 1


def test_finger_regression_windows(fake_reg):
    paradigm = FingerFlexionRegression(fmin=1.0, fmax=100.0, window_size=0.4, window_stride=0.1)
    assert paradigm.is_valid(fake_reg)
    X, y, meta = paradigm.get_data(fake_reg)
    n_times = int(40.0 * 250)
    n_win = (n_times - 100) // 25 + 1
    assert X.shape == (n_win, 6, 100)
    assert y.shape == (n_win, 5)
    # causal: target at window end
    raw = fake_reg.get_data(subjects=[1])[1]["0"]["0"]
    flex = raw.get_data(picks="misc").T
    np.testing.assert_allclose(y[3], flex[3 * 25 + 99])


def test_cursor_regression_velocity():
    ds = FakeECoGDataset(n_subjects=1, n_channels=4, sfreq=250.0, paradigm="cursor_regression",
                         duration=10.0, n_targets=2, seed=3)
    paradigm = CursorRegression(fmin=1.0, fmax=100.0, target="velocity")
    assert paradigm.is_valid(ds)
    X, y, _ = paradigm.get_data(ds)
    assert y.shape[1] == 2
    pos = CursorRegression(fmin=1.0, fmax=100.0, target="position").get_data(ds)[1]
    assert not np.allclose(pos, y)
    with pytest.raises(ValueError):
        CursorRegression(target="speed")
