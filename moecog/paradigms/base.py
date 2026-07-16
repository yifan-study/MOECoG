"""Base paradigm classes for classification and regression tasks."""

from abc import ABC, abstractmethod

import mne
import numpy as np
import pandas as pd


class BaseParadigm(ABC):
    """Base class for all paradigms.

    Transforms raw ECoG data from a dataset into ``(X, y, metadata)`` arrays
    ready for scikit-learn pipelines.

    Parameters
    ----------
    fmin : float
        Lower bandpass frequency in Hz.
    fmax : float
        Upper bandpass frequency in Hz.
    resample : float or None
        Target sampling rate in Hz. None keeps the original rate.
    channels : list of str or None
        Channel names to select. None uses all ECoG channels.
    """

    def __init__(
        self,
        fmin: float = 0.5,
        fmax: float = 200.0,
        resample: float | None = None,
        channels: list[str] | None = None,
    ):
        self.fmin = fmin
        self.fmax = fmax
        self.resample = resample
        self.channels = channels

    @abstractmethod
    def get_data(self, dataset, subjects=None):
        """Extract (X, y, metadata) from a dataset.

        Returns
        -------
        X : np.ndarray
        y : np.ndarray
        metadata : pd.DataFrame
        """

    @abstractmethod
    def is_valid(self, dataset) -> bool:
        """Check if a dataset is compatible with this paradigm."""

    @abstractmethod
    def scoring(self):
        """Return scoring metric name(s)."""

    @property
    @abstractmethod
    def datasets(self) -> list:
        """Return list of compatible dataset classes."""

    def _preprocess_raw(self, raw):
        """Apply bandpass filter, channel selection, and resampling."""
        raw = raw.copy()
        raw.filter(self.fmin, self.fmax, verbose=False)
        if self.channels:
            raw.pick_channels(self.channels)
        if self.resample:
            raw.resample(self.resample, verbose=False)
        return raw


class BaseClassificationParadigm(BaseParadigm):
    """Base paradigm for epoched classification tasks.

    Parameters
    ----------
    tmin : float
        Epoch start time relative to event onset (seconds).
    tmax : float or None
        Epoch end time relative to event onset (seconds).
    baseline : tuple or None
        Baseline correction window.
    """

    def __init__(self, tmin=0.0, tmax=None, baseline=None, **kwargs):
        super().__init__(**kwargs)
        self.tmin = tmin
        self.tmax = tmax
        self.baseline = baseline

    @abstractmethod
    def used_events(self, dataset):
        """Return the event dict this paradigm uses from the dataset."""

    def get_data(self, dataset, subjects=None):
        subjects = subjects or dataset.subject_list
        all_X, all_y, all_meta = [], [], []

        for subject in subjects:
            sub_data = dataset.get_data(subjects=[subject])
            for session_id, runs in sub_data[subject].items():
                for run_id, raw in runs.items():
                    raw = self._preprocess_raw(raw)
                    events, _ = mne.events_from_annotations(raw, verbose=False)
                    used = self.used_events(dataset)
                    tmax = self.tmax if self.tmax is not None else dataset.interval[1]
                    epochs = mne.Epochs(
                        raw,
                        events,
                        event_id=used,
                        tmin=self.tmin,
                        tmax=tmax,
                        baseline=self.baseline,
                        preload=True,
                        verbose=False,
                    )
                    X = epochs.get_data(copy=False)
                    y = np.array(
                        [
                            list(used.keys())[list(used.values()).index(e)]
                            for e in epochs.events[:, 2]
                        ]
                    )
                    meta = pd.DataFrame(
                        {"subject": subject, "session": session_id, "run": run_id},
                        index=range(len(y)),
                    )
                    all_X.append(X)
                    all_y.append(y)
                    all_meta.append(meta)

        return (
            np.concatenate(all_X),
            np.concatenate(all_y),
            pd.concat(all_meta).reset_index(drop=True),
        )


class BaseRegressionParadigm(BaseParadigm):
    """Base paradigm for continuous regression tasks.

    Uses causal windowing: target ``y[i]`` is the value at the **end** of
    window ``i``, ensuring the model only sees past neural data.

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
        """Extract continuous target signals from a Raw object.

        Returns
        -------
        np.ndarray, shape (n_samples, n_targets)
        """

    def get_data(self, dataset, subjects=None):
        subjects = subjects or dataset.subject_list
        all_X, all_y, all_meta = [], [], []

        for subject in subjects:
            sub_data = dataset.get_data(subjects=[subject])
            for session_id, runs in sub_data[subject].items():
                for run_id, raw in runs.items():
                    raw = self._preprocess_raw(raw)
                    targets = self._extract_targets(raw, dataset)

                    sfreq = raw.info["sfreq"]
                    data = raw.pick(picks="ecog", exclude=[]).get_data()
                    win_samples = int(self.window_size * sfreq)
                    stride_samples = int(self.window_stride * sfreq)

                    n_windows = (data.shape[1] - win_samples) // stride_samples + 1
                    X = np.zeros((n_windows, data.shape[0], win_samples))
                    y = np.zeros((n_windows, targets.shape[1]))

                    for i in range(n_windows):
                        start = i * stride_samples
                        end = start + win_samples
                        X[i] = data[:, start:end]
                        # Causal: target at end of window
                        y[i] = targets[min(end, targets.shape[0] - 1)]

                    meta = pd.DataFrame(
                        {"subject": subject, "session": session_id, "run": run_id},
                        index=range(n_windows),
                    )
                    all_X.append(X)
                    all_y.append(y)
                    all_meta.append(meta)

        return (
            np.concatenate(all_X),
            np.concatenate(all_y),
            pd.concat(all_meta).reset_index(drop=True),
        )
