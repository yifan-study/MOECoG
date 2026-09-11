"""Braindecode models as scikit-learn estimators (CPU by default).

``BraindecodeClassifier`` wraps a braindecode model (``ShallowFBCSPNet``, ``Deep4Net``, ``EEGNetv4`` and any other
class in ``braindecode.models`` that takes ``n_chans``, ``n_outputs``, ``n_times``) in a scikit-learn classifier:
``fit(X, y)`` with ``X`` of shape (n_trials, n_channels, n_times), per-channel standardisation learned on the
training set, labels encoded internally, a fixed number of epochs (no early stopping, so no peeking at the test
fold), and a seed for every source of randomness. Import cost is paid on first use, not on ``import moecog``.
"""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import LabelEncoder


class BraindecodeClassifier(BaseEstimator, ClassifierMixin):
    """Fixed-budget braindecode classifier.

    Parameters
    ----------
    model : str
        Class name in ``braindecode.models``.
    n_epochs : int
        Training epochs (fixed; there is no validation split).
    lr, weight_decay, batch_size : float, float, int
        AdamW settings.
    random_state : int
        Seeds numpy and torch.
    device : str
        ``"cpu"`` (default), ``"cuda"`` or ``"mps"``.
    model_kwargs : dict or None
        Extra keyword arguments for the model class.
    """

    def __init__(self, model="ShallowFBCSPNet", n_epochs=40, lr=0.000625, weight_decay=0.0, batch_size=32,
                 random_state=0, device="cpu", model_kwargs=None):
        self.model = model
        self.n_epochs = n_epochs
        self.lr = lr
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.random_state = random_state
        self.device = device
        self.model_kwargs = model_kwargs

    def _standardise(self, X, fit=False):
        X = np.asarray(X, dtype=np.float32)
        if fit:
            self.mean_ = X.mean(axis=(0, 2), keepdims=True)
            self.std_ = X.std(axis=(0, 2), keepdims=True) + 1e-6
        return (X - self.mean_) / self.std_

    @staticmethod
    def _tensor(X, dtype=None):
        """numpy -> torch without relying on torch's numpy bridge (absent in torch <= 2.2 with NumPy 2)."""
        import torch

        X = np.ascontiguousarray(X)
        try:
            t = torch.from_numpy(X)
        except RuntimeError:
            t = torch.tensor(X.tolist())
        return t.to(dtype) if dtype is not None else t

    def fit(self, X, y):
        import torch
        from braindecode import EEGClassifier
        from braindecode import models as bd_models

        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)
        self.encoder_ = LabelEncoder().fit(y)
        y_enc = self.encoder_.transform(y).astype(np.int64)
        X = self._standardise(X, fit=True)
        n_trials, n_chans, n_times = X.shape
        cls = getattr(bd_models, self.model)
        kwargs = dict(self.model_kwargs or {})
        net = cls(n_chans=n_chans, n_outputs=len(self.encoder_.classes_), n_times=n_times, **kwargs)
        self.classes_ = self.encoder_.classes_
        self.clf_ = EEGClassifier(
            net, criterion=torch.nn.CrossEntropyLoss, optimizer=torch.optim.AdamW,
            optimizer__lr=self.lr, optimizer__weight_decay=self.weight_decay, batch_size=self.batch_size,
            max_epochs=self.n_epochs, train_split=None, device=self.device, verbose=0, callbacks=[],
        )
        import torch as _torch

        self.clf_.fit(self._tensor(X, _torch.float32), self._tensor(y_enc, _torch.long))
        return self

    def predict_proba(self, X):
        import torch

        X = self._tensor(self._standardise(X), torch.float32)
        module = self.clf_.module_.eval()
        out = []
        with torch.no_grad():
            for start in range(0, len(X), self.batch_size):
                logits = module(X[start:start + self.batch_size].to(self.device))
                out.append(torch.softmax(logits, dim=1).cpu())
        return np.asarray(torch.cat(out).tolist(), dtype=float)

    def predict(self, X):
        return self.encoder_.inverse_transform(np.argmax(self.predict_proba(X), axis=1))
