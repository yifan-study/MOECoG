"""Continuous regression paradigms (finger flexion, cursor kinematics)."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter1d

from moecog.datasets.miller_library import FINGERS

from .base import BaseRegressionParadigm


class FingerFlexionRegression(BaseRegressionParadigm):
    """Predict dataglove finger flexion from ECoG windows.

    Headline metric: Pearson r averaged over fingers (the BCI-IV convention).

    Targets are the ``flex_<finger>`` misc channels (Miller fingerflex) or
    ``dg_<finger>`` (gestures). Metrics: Pearson r (mean over fingers), R^2.
    """

    def __init__(self, fmin=1.0, fmax=200.0, window_size=0.5, window_stride=0.05,
                 fingers=FINGERS, resample=None, channels=None):
        super().__init__(window_size=window_size, window_stride=window_stride, fmin=fmin,
                         fmax=fmax, resample=resample, channels=channels)
        self.fingers = list(fingers)

    headline_metric = "pearson_r"

    def _target_names(self, raw):
        for prefix in ("flex", "dg"):
            names = [f"{prefix}_{f}" for f in self.fingers]
            if all(n in raw.ch_names for n in names):
                return names
        raise ValueError(f"No finger target channels for {self.fingers} in {raw.ch_names}")

    def _extract_targets(self, raw, dataset):
        return raw.get_data(picks=self._target_names(raw)).T

    def is_valid(self, dataset):
        return dataset.paradigm_type == "motor_regression"

    def scoring(self):
        return ["pearson_r", "r2"]

    @property
    def datasets(self):
        from moecog.datasets import MillerLibrary

        return [MillerLibrary]


class CursorRegression(BaseRegressionParadigm):
    """Predict 2-D cursor kinematics (joystick_track, mouse_track).

    Parameters
    ----------
    target : {"velocity", "position"}
        Velocity is the default: motor cortex encodes movement, and absolute
        screen position is non-stationary (PACE, 2026). Position is smoothed
        with a ``smooth_ms`` moving average before differentiation, otherwise
        the 16-bit quantised trace yields pure quantisation noise.
    """

    def __init__(self, target="velocity", smooth_ms=31.0, fmin=1.0, fmax=200.0,
                 window_size=0.5, window_stride=0.05, resample=None, channels=None):
        super().__init__(window_size=window_size, window_stride=window_stride, fmin=fmin,
                         fmax=fmax, resample=resample, channels=channels)
        if target not in ("velocity", "position"):
            raise ValueError("target must be 'velocity' or 'position'")
        self.target = target
        self.smooth_ms = smooth_ms

    headline_metric = "pearson_r"

    def _extract_targets(self, raw, dataset):
        pos = raw.get_data(picks=["CursorPosX", "CursorPosY"]).T
        if self.target == "position":
            return pos
        n = max(1, int(round(self.smooth_ms * raw.info["sfreq"] / 1000.0)))
        smooth = uniform_filter1d(pos, size=n, axis=0, mode="nearest")
        return np.gradient(smooth, axis=0)

    def is_valid(self, dataset):
        return dataset.paradigm_type == "cursor_regression"

    def scoring(self):
        return ["pearson_r", "r2"]

    @property
    def datasets(self):
        from moecog.datasets import MillerLibrary

        return [MillerLibrary]
