"""Base paradigm classes for classification and regression tasks."""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod

import mne
import numpy as np
import pandas as pd


def _stack_subjects(all_X, all_y, all_meta, dataset):
    """Concatenate per-run arrays, refusing ragged channel counts across subjects."""
    n_ch = {int(x.shape[1]) for x in all_X}
    if len(n_ch) > 1:
        raise ValueError(
            f"{dataset.code}: subjects have different channel counts {sorted(n_ch)}; "
            "ECoG montages are patient-specific, so load one subject at a time "
            "(evaluations do this by default) or align channels first."
        )
    n_times = min(x.shape[2] for x in all_X)
    all_X = [x[:, :, :n_times] for x in all_X]
    return (
        np.concatenate(all_X),
        np.concatenate(all_y),
        pd.concat(all_meta).reset_index(drop=True),
    )


class BaseParadigm(ABC):
    """Base class for all paradigms.

    Transforms raw ECoG data from a dataset into ``(X, y, metadata)`` arrays
    ready for scikit-learn pipelines.

    Parameters
    ----------
    fmin : float
        Lower band-pass frequency in Hz.
    fmax : float or None
        Upper band-pass frequency in Hz. Clamped below the Nyquist frequency
        of each recording (the Miller amplifiers already low-pass at 200 Hz).
    resample : float or None
        Target sampling rate in Hz. None keeps the original rate.
    channels : list of str or None
        Channel names to select. None uses all ECoG channels.
    """

    def __init__(
        self,
        fmin: float = 0.5,
        fmax: float | None = 200.0,
        resample: float | None = None,
        channels: list[str] | None = None,
    ):
        self.fmin = fmin
        self.fmax = fmax
        self.resample = resample
        self.channels = channels

    @abstractmethod
    def get_data(self, dataset, subjects=None):
        """Extract ``(X, y, metadata)`` from a dataset."""

    @abstractmethod
    def is_valid(self, dataset) -> bool:
        """Check if a dataset is compatible with this paradigm."""

    @abstractmethod
    def scoring(self):
        """Return the metric name or list of metric names."""

    @property
    @abstractmethod
    def datasets(self) -> list:
        """Return list of compatible dataset classes."""

    def _preprocess_raw(self, raw):
        """Band-pass the ECoG channels, select channels, resample."""
        raw = raw.copy()
        nyq = raw.info["sfreq"] / 2.0
        h_freq = self.fmax if (self.fmax is not None and self.fmax < nyq) else None
        l_freq = self.fmin if (self.fmin is not None and self.fmin > 0) else None
        if l_freq is not None or h_freq is not None:
            raw.filter(l_freq, h_freq, picks=["ecog"], verbose=False)
        if self.channels:
            keep = [c for c in raw.ch_names if c in self.channels or
                    raw.get_channel_types([c])[0] != "ecog"]
            raw.pick(keep)
        if self.resample:
            raw.resample(self.resample, verbose=False)
        return raw


class BaseClassificationParadigm(BaseParadigm):
    """Base paradigm for epoched classification tasks.

    Trials are cut from the annotations that datasets attach to each Raw
    (``mne.events_from_annotations``); only ``ecog`` channels enter ``X``.

    Parameters
    ----------
    tmin : float
        Epoch start relative to cue onset (seconds).
    tmax : float or None
        Epoch end relative to cue onset. None uses the dataset's ``interval``.
    baseline : tuple or None
        Baseline correction window.
    """

    def __init__(self, tmin=0.0, tmax=None, baseline=None, **kwargs):
        super().__init__(**kwargs)
        self.tmin = tmin
        self.tmax = tmax
        self.baseline = baseline

    @abstractmethod
    def used_events(self, dataset) -> dict[str, int]:
        """Return the ``{name: id}`` subset of ``dataset.event_id`` this paradigm uses."""

    def _epoch_run(self, raw, dataset, subject, session_id, run_id):
        used = self.used_events(dataset)
        raw = self._preprocess_raw(raw)
        try:
            events, _ = mne.events_from_annotations(raw, event_id=used, verbose=False)
        except ValueError:
            return None
        if len(events) == 0:
            return None
        tmax = self.tmax if self.tmax is not None else dataset.interval[1]
        picks = mne.pick_types(raw.info, ecog=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            epochs = mne.Epochs(
                raw, events, event_id={k: v for k, v in used.items() if v in events[:, 2]},
                tmin=self.tmin, tmax=tmax, baseline=self.baseline, picks=picks,
                preload=True, event_repeated="drop", verbose=False,
            )
        if len(epochs) == 0:
            return None
        X = epochs.get_data(copy=False)
        inv = {v: k for k, v in used.items()}
        y = np.array([inv[e] for e in epochs.events[:, 2]])
        sfreq = raw.info["sfreq"]
        meta = pd.DataFrame({
            "subject": subject,
            "session": session_id,
            "run": run_id,
            "trial": np.arange(len(y)),
            "onset": epochs.events[:, 0] / sfreq,
        })
        return X, y, meta

    def get_data(self, dataset, subjects=None):
        subjects = subjects if subjects is not None else dataset.subject_list
        all_X, all_y, all_meta = [], [], []
        for subject in subjects:
            sub_data = dataset.get_data(subjects=[subject])
            for session_id, runs in sub_data[subject].items():
                for run_id, raw in runs.items():
                    out = self._epoch_run(raw, dataset, subject, session_id, run_id)
                    if out is None:
                        continue
                    all_X.append(out[0])
                    all_y.append(out[1])
                    all_meta.append(out[2])
        if not all_X:
            raise ValueError(
                f"No trials found in {dataset.code} for events {list(self.used_events(dataset))}"
            )
        return _stack_subjects(all_X, all_y, all_meta, dataset)


class BaseRegressionParadigm(BaseParadigm):
    """Base paradigm for continuous regression tasks.

    Uses causal windowing: target ``y[i]`` is the value at the **end** of
    window ``i``, so the model only sees past neural data.

    Parameters
    ----------
    window_size : float
        Window length in seconds.
    window_stride : float
        Stride between windows in seconds.
    """

    def __init__(self, window_size=0.5, window_stride=0.05, **kwargs):
        super().__init__(**kwargs)
        self.window_size = window_size
        self.window_stride = window_stride

    @abstractmethod
    def _extract_targets(self, raw, dataset):
        """Return the continuous targets, shape ``(n_times, n_targets)``."""

    def get_data(self, dataset, subjects=None):
        subjects = subjects if subjects is not None else dataset.subject_list
        all_X, all_y, all_meta = [], [], []

        for subject in subjects:
            sub_data = dataset.get_data(subjects=[subject])
            for session_id, runs in sub_data[subject].items():
                for run_id, raw in runs.items():
                    raw = self._preprocess_raw(raw)
                    targets = np.asarray(self._extract_targets(raw, dataset), dtype=float)
                    if targets.ndim == 1:
                        targets = targets[:, None]

                    sfreq = raw.info["sfreq"]
                    data = raw.get_data(picks="ecog")
                    win = int(round(self.window_size * sfreq))
                    stride = max(1, int(round(self.window_stride * sfreq)))
                    n_windows = (data.shape[1] - win) // stride + 1
                    if n_windows <= 0:
                        continue
                    starts = np.arange(n_windows) * stride
                    idx = starts[:, None] + np.arange(win)[None, :]
                    X = data[:, idx].transpose(1, 0, 2)  # (n_windows, n_ch, win)
                    ends = np.minimum(starts + win - 1, targets.shape[0] - 1)
                    y = targets[ends]
                    meta = pd.DataFrame({
                        "subject": subject,
                        "session": session_id,
                        "run": run_id,
                        "trial": np.arange(n_windows),
                        "onset": ends / sfreq,
                    })
                    all_X.append(X)
                    all_y.append(y)
                    all_meta.append(meta)

        if not all_X:
            raise ValueError(f"No windows produced for {dataset.code}")
        return _stack_subjects(all_X, all_y, all_meta, dataset)
