"""Label-free session alignment: recentre each session's trial covariances before any pipeline sees the data.

Why: band power standardised on one session does not transfer to the next (BCI III-1: kappa 0.80 within a
session, 0.00 to 0.36 a week later, `docs/baselines.md`). Alignment maps every session to a common reference
using only that session's own unlabeled trials, so it applies to the test session as well.

Methods (``ALIGNMENTS``):

* ``"ea"``: Euclidean alignment (He and Wu 2020, doi:10.1109/TBME.2019.2913914). ``R`` is the arithmetic mean of
  the trial covariances of a session, every trial becomes ``R^{-1/2} X``; the aligned session has mean covariance
  identity.
* ``"recenter"``: Riemannian re-centering (Zanini et al. 2018, doi:10.1109/TBME.2017.2742541; the first step of
  Riemannian Procrustes Analysis, Rodrigues et al. 2019). Same whitening with the Riemannian mean of the trial
  covariances (needs pyriemann).
* ``"zscore"``: per-channel standardisation of each session (diagonal whitening); the ablation that tells whether
  the full covariance matters or only the per-channel scale.

All operate on arrays of shape ``(n_trials, n_channels, n_times)`` and return the aligned array of the same shape.
Evaluations take ``alignment="ea"`` and apply it per (patient, session) after the paradigm's filtering and epoching;
``benchmark()`` spells it ``evaluations=("cross_session:ea",)``.
"""

from __future__ import annotations

import numpy as np


def trial_covariances(X, reg: float = 1e-8):
    """Sample covariance of each trial, ``(n_trials, n_channels, n_channels)``, with a small ridge."""
    X = np.asarray(X, dtype=float)
    X = X - X.mean(axis=-1, keepdims=True)
    C = np.einsum("nct,ndt->ncd", X, X) / X.shape[-1]
    return C + reg * np.trace(C, axis1=1, axis2=2)[:, None, None] / X.shape[1] * np.eye(X.shape[1])


def _inv_sqrt(R, eps: float = 1e-10):
    w, V = np.linalg.eigh((R + R.T) / 2.0)
    w = np.maximum(w, eps * w.max())
    return (V / np.sqrt(w)) @ V.T


def euclidean_alignment(X, reg: float = 1e-8):
    """Whiten a session by the arithmetic mean of its trial covariances (He and Wu 2020)."""
    R = trial_covariances(X, reg).mean(axis=0)
    return np.einsum("cd,ndt->nct", _inv_sqrt(R), np.asarray(X, dtype=float))


def riemannian_recentering(X, reg: float = 1e-8):
    """Whiten a session by the Riemannian mean of its trial covariances (Zanini et al. 2018)."""
    try:
        from pyriemann.utils.mean import mean_riemann
    except ImportError as err:  # pragma: no cover - optional dependency
        raise ImportError("alignment='recenter' needs pyriemann (pip install moecog[riemann])") from err
    R = mean_riemann(trial_covariances(X, reg))
    return np.einsum("cd,ndt->nct", _inv_sqrt(R), np.asarray(X, dtype=float))


def zscore_alignment(X, eps: float = 1e-12):
    """Standardise every channel of a session over all its trials and samples (diagonal whitening)."""
    X = np.asarray(X, dtype=float)
    mu = X.mean(axis=(0, 2), keepdims=True)
    sd = X.std(axis=(0, 2), keepdims=True) + eps
    return (X - mu) / sd


ALIGNMENTS = {"ea": euclidean_alignment, "recenter": riemannian_recentering, "zscore": zscore_alignment}


def align_sessions(X, sessions, method: str | None):
    """Apply ``method`` to every session of ``X`` separately (``sessions`` labels each trial); None returns X."""
    if method is None:
        return X
    if method not in ALIGNMENTS:
        raise ValueError(f"unknown alignment {method!r}; choose from {sorted(ALIGNMENTS)}")
    X = np.asarray(X, dtype=float)
    if X.ndim != 3:
        raise ValueError(f"alignment needs (n_trials, n_channels, n_times) arrays, got shape {X.shape}")
    out = np.empty_like(X)
    sessions = np.asarray(sessions)
    for s in np.unique(sessions):
        m = sessions == s
        out[m] = ALIGNMENTS[method](X[m])
    return out


__all__ = ["ALIGNMENTS", "align_sessions", "euclidean_alignment", "riemannian_recentering", "zscore_alignment",
           "trial_covariances"]
