"""Log band-power features."""

from __future__ import annotations

import numpy as np
from scipy.signal import welch
from sklearn.base import BaseEstimator, TransformerMixin

DEFAULT_BANDS = {
    "mu": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "low_gamma": (30.0, 70.0),
    "high_gamma": (70.0, 150.0),
}


class LogBandPower(BaseEstimator, TransformerMixin):
    """Log10 Welch power in canonical ECoG bands, per channel.

    Input ``(n_samples, n_channels, n_times)``, output
    ``(n_samples, n_channels * n_bands)``. Stateless.

    Parameters
    ----------
    bands : dict or None
        ``{name: (fmin, fmax)}``; defaults to mu, beta, low and high gamma.
        Bands above the Nyquist frequency are dropped.
    sfreq : float
        Sampling rate of the windows (after any paradigm resampling).
    nperseg : int or None
        Welch segment length; defaults to ``min(256, n_times)``.
    """

    def __init__(self, bands=None, sfreq=1000.0, nperseg=None):
        self.bands = bands
        self.sfreq = sfreq
        self.nperseg = nperseg

    def fit(self, X, y=None):
        return self

    def _bands(self):
        bands = self.bands or DEFAULT_BANDS
        return {k: v for k, v in bands.items() if v[0] < self.sfreq / 2}

    def transform(self, X):
        X = np.asarray(X)
        if X.ndim != 3:
            raise ValueError(f"Expected (n_samples, n_channels, n_times), got {X.shape}")
        n_times = X.shape[-1]
        nperseg = min(self.nperseg or 256, n_times)
        freqs, psd = welch(X, fs=self.sfreq, nperseg=nperseg, axis=-1)
        feats = []
        for lo, hi in self._bands().values():
            mask = (freqs >= lo) & (freqs <= min(hi, self.sfreq / 2))
            if not mask.any():
                mask = np.argmin(np.abs(freqs - lo))
            feats.append(np.log10(psd[..., mask].mean(axis=-1) + 1e-30))
        return np.stack(feats, axis=-1).reshape(X.shape[0], -1)


class HighGammaPower(LogBandPower):
    """Log high-gamma (70-150 Hz) power only, the standard ECoG motor feature."""

    def __init__(self, sfreq=1000.0, nperseg=None, fmin=70.0, fmax=150.0):
        super().__init__(bands={"high_gamma": (fmin, fmax)}, sfreq=sfreq, nperseg=nperseg)
        self.fmin = fmin
        self.fmax = fmax
