"""Preprocessing steps mirroring the pipelines of the source groups.

Two kinds of objects:

* **Raw-level steps** (``RawStep`` subclasses) operate on an :class:`mne.io.Raw`
  before epoching or windowing: re-referencing and notch filtering. Pass them
  to any paradigm as ``raw_steps=[CommonAverageReference(), NotchFilter()]``.
* **Feature transformers** (scikit-learn) operate on windows or epochs of shape
  ``(n_samples, n_channels, n_times)`` inside a pipeline.

See ``docs/preprocessing_catalog.md`` for the field survey these mirror.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, decimate, hilbert, sosfiltfilt
from sklearn.base import BaseEstimator, TransformerMixin


class RawStep:
    """Base class for Raw-level preprocessing steps."""

    def apply(self, raw):  # pragma: no cover - interface
        raise NotImplementedError

    def __call__(self, raw):
        return self.apply(raw)


class CommonAverageReference(RawStep):
    """Subtract the mean of the ECoG channels (optionally per channel group).

    Parameters
    ----------
    groups : list of list of str or None
        Channel-name groups referenced separately (Chang-lab style per
        amplifier block). None uses one group of all ECoG channels. Bad
        channels listed in ``raw.info["bads"]`` are excluded from the mean.
    """

    def __init__(self, groups=None):
        self.groups = groups

    def apply(self, raw):
        import mne

        raw = raw.copy() if not raw.preload else raw
        raw.load_data()
        picks = mne.pick_types(raw.info, ecog=True, exclude="bads")
        names = [raw.ch_names[i] for i in picks]
        groups = self.groups or [names]
        data = raw._data
        for group in groups:
            idx = [raw.ch_names.index(n) for n in group if n in names]
            if len(idx) < 2:
                continue
            data[idx] -= data[idx].mean(axis=0, keepdims=True)
        return raw


class NotchFilter(RawStep):
    """Notch out line noise and harmonics on the ECoG channels."""

    def __init__(self, freqs=(60.0, 120.0, 180.0), notch_widths=None):
        self.freqs = tuple(freqs)
        self.notch_widths = notch_widths

    def apply(self, raw):
        raw.load_data()
        nyq = raw.info["sfreq"] / 2.0
        freqs = [f for f in self.freqs if f < nyq]
        if freqs:
            raw.notch_filter(freqs, picks=["ecog"], notch_widths=self.notch_widths,
                             verbose=False)
        return raw


def apply_raw_steps(raw, steps):
    """Apply a sequence of :class:`RawStep` (or callables) to ``raw``."""
    for step in steps or ():
        raw = step(raw)
    return raw


class HilbertEnvelope(BaseEstimator, TransformerMixin):
    """Analytic-amplitude envelopes of one or more bands.

    Input ``(n_samples, n_channels, n_times)``; output
    ``(n_samples, n_channels * n_bands, n_times_out)`` or, with
    ``average=True``, ``(n_samples, n_channels * n_bands)``.

    Parameters
    ----------
    bands : dict
        ``{name: (fmin, fmax)}``. Bands above Nyquist are dropped.
    sfreq : float
    order : int
        Butterworth order (applied forward-backward).
    log : bool
        Take ``log`` of the envelope.
    decimate : int or None
        Integer decimation factor of the envelope time axis.
    average : bool
        Return the time-averaged envelope per channel and band.
    zscore : bool
        Standardise each channel-band feature over samples (fit on training
        data, as a scikit-learn transformer should).
    """

    def __init__(self, bands=None, sfreq=1000.0, order=4, log=True, decimate=None,
                 average=False, zscore=False):
        self.bands = bands
        self.sfreq = sfreq
        self.order = order
        self.log = log
        self.decimate = decimate
        self.average = average
        self.zscore = zscore

    def _bands(self):
        bands = self.bands or {"high_gamma": (70.0, 150.0)}
        nyq = self.sfreq / 2.0
        return {k: (lo, min(hi, 0.98 * nyq)) for k, (lo, hi) in bands.items() if lo < nyq}

    def _envelopes(self, X):
        X = np.asarray(X, dtype=float)
        outs = []
        for lo, hi in self._bands().values():
            sos = butter(self.order, [lo, hi], btype="bandpass", fs=self.sfreq, output="sos")
            filt = sosfiltfilt(sos, X, axis=-1)
            env = np.abs(hilbert(filt, axis=-1))
            if self.decimate and self.decimate > 1 and not self.average:
                env = decimate(env, int(self.decimate), axis=-1, zero_phase=True)
            outs.append(env)
        env = np.concatenate(outs, axis=1)  # (n, ch * bands, t)
        if self.log:
            env = np.log(env + 1e-12)
        if self.average:
            env = env.mean(axis=-1)
        return env

    def fit(self, X, y=None):
        if self.zscore:
            feats = self._envelopes(X)
            self.mean_ = feats.mean(axis=0, keepdims=True)
            self.std_ = feats.std(axis=0, keepdims=True) + 1e-12
        return self

    def transform(self, X):
        feats = self._envelopes(X)
        if self.zscore:
            feats = (feats - self.mean_) / self.std_
        return feats


def chang_high_gamma(sfreq=1000.0, n_bands=8, fmin=70.0, fmax=150.0, decimate=None,
                     average=False):
    """Chang-lab high gamma: 8 log-spaced sub-bands 70-150 Hz, averaged, z-scored.

    Returns a transformer producing one high-gamma feature per channel.
    """
    edges = np.logspace(np.log10(fmin), np.log10(fmax), n_bands + 1)
    bands = {f"hg{i}": (float(edges[i]), float(edges[i + 1])) for i in range(n_bands)}
    return _AveragedBands(HilbertEnvelope(bands=bands, sfreq=sfreq, log=False,
                                          decimate=decimate, average=average),
                          n_bands=n_bands)


class _AveragedBands(BaseEstimator, TransformerMixin):
    """Average the sub-band envelopes of a :class:`HilbertEnvelope` per channel."""

    def __init__(self, envelope, n_bands):
        self.envelope = envelope
        self.n_bands = n_bands

    def fit(self, X, y=None):
        self.envelope.fit(X)
        feats = self._avg(self.envelope.transform(X))
        self.mean_ = feats.mean(axis=0, keepdims=True)
        self.std_ = feats.std(axis=0, keepdims=True) + 1e-12
        return self

    def _avg(self, env):
        n, chb = env.shape[0], env.shape[1]
        n_ch = chb // self.n_bands
        # HilbertEnvelope concatenates band blocks: [band0 ch0..chN, band1 ch0..chN, ...]
        env = env.reshape((n, self.n_bands, n_ch) + env.shape[2:])
        return env.mean(axis=1)

    def transform(self, X):
        feats = self._avg(self.envelope.transform(X))
        return (feats - self.mean_) / self.std_


__all__ = [
    "RawStep",
    "CommonAverageReference",
    "NotchFilter",
    "apply_raw_steps",
    "HilbertEnvelope",
    "chang_high_gamma",
]
