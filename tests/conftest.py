"""Shared test fixtures."""

import os
from pathlib import Path

import pytest

from moecog.datasets import FakeECoGDataset


@pytest.fixture(scope="session")
def fake_cls():
    return FakeECoGDataset(n_subjects=2, n_channels=8, sfreq=250.0, paradigm="motor_execution",
                           n_trials_per_class=12, trial_duration=1.0, isi=0.5, seed=1)


@pytest.fixture(scope="session")
def fake_reg():
    return FakeECoGDataset(n_subjects=1, n_channels=6, sfreq=250.0, paradigm="motor_regression",
                           duration=40.0, n_targets=5, seed=2)


def miller_root():
    """Root of the extracted Miller library if available locally, else None."""
    env = os.environ.get("MOECOG_MILLER_DIR")
    if env and Path(env).is_dir():
        return Path(env)
    return None


needs_miller = pytest.mark.skipif(miller_root() is None, reason="MOECOG_MILLER_DIR not set")
