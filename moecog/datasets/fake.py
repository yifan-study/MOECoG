"""Synthetic ECoG dataset for tests and examples (no download needed)."""

from __future__ import annotations

import hashlib

import mne
import numpy as np

from .base import BaseECoGDataset, ElectrodeInfo
from .miller_library import FINGERS, annotations_from_codes

REGRESSION_PARADIGMS = ("motor_regression", "cursor_regression")


class FakeECoGDataset(BaseECoGDataset):
    """Generate ECoG-like data with a known, decodable structure.

    Classification paradigms (default): cued trials where class ``k`` adds a
    narrow-band oscillation (``class_freqs[k]``) to its own subset of channels.
    Regression paradigms (``paradigm`` in ``("motor_regression",
    "cursor_regression")``): smooth random targets that amplitude-modulate a
    70 Hz carrier, so high-gamma power tracks the target. Targets are exposed
    as ``misc`` channels named like the Miller loaders (``flex_<finger>`` or
    ``CursorPosX``/``CursorPosY``).

    Parameters
    ----------
    n_subjects, n_sessions, n_runs : int
    n_channels : int or dict
        Channels per subject; a ``{subject: n}`` dict gives every patient its
        own grid size, as in real ECoG.
    sfreq : float
    paradigm : str
    events : dict or None
        ``{name: code}`` for classification; default ``{"hand": 1, "tongue": 2}``.
    n_trials_per_class : int
    trial_duration, isi : float
        Seconds.
    duration : float
        Recording length in seconds for regression data.
    n_targets : int
        Number of regression targets (5 -> finger names, 2 -> cursor names).
    snr : float
        Amplitude of the class/target signal relative to the noise std.
    cue_order : {"interleaved", "blocked"}
        Blocked presents all trials of a class before the next class, as a
        few library files do.
    seed : int
    """

    def __init__(
        self,
        n_subjects=2,
        n_sessions=1,
        n_runs=1,
        n_channels=8,
        sfreq=250.0,
        paradigm="motor_execution",
        events=None,
        n_trials_per_class=12,
        trial_duration=1.0,
        isi=1.0,
        duration=60.0,
        n_targets=5,
        snr=2.0,
        seed=0,
        cue_order="interleaved",
    ):
        self.is_regression = paradigm in REGRESSION_PARADIGMS
        if events is None:
            events = None if self.is_regression else {"hand": 1, "tongue": 2}
        self._n_channels = n_channels
        self.n_channels = n_channels if isinstance(n_channels, int) else max(n_channels.values())
        self.n_runs = n_runs
        self.n_trials_per_class = n_trials_per_class
        self.trial_duration = trial_duration
        self.isi = isi
        self.duration = duration
        self.n_targets = n_targets
        self.snr = snr
        self.seed = seed
        if cue_order not in ("interleaved", "blocked"):
            raise ValueError("cue_order must be 'interleaved' or 'blocked'")
        self.cue_order = cue_order
        self.class_freqs = [12.0, 30.0, 45.0, 70.0, 90.0, 20.0, 55.0, 80.0]
        interval = None if self.is_regression else [0.0, trial_duration]
        super().__init__(
            subjects=list(range(1, n_subjects + 1)),
            sessions_per_subject=n_sessions,
            events=events,
            code="FakeECoG",
            paradigm=paradigm,
            interval=interval,
            sfreq=sfreq,
        )

    # -- helpers -------------------------------------------------------------
    def _rng(self, subject, session, run):
        key = f"{self.seed}-{subject}-{session}-{run}".encode()
        return np.random.default_rng(int(hashlib.md5(key).hexdigest()[:8], 16))

    def _noise(self, rng, n_ch, n_times):
        white = rng.standard_normal((n_ch, n_times))
        # mild 1/f colouring
        return white + 0.5 * np.cumsum(white, axis=1) / np.sqrt(np.arange(1, n_times + 1))

    def _n_ch(self, subject):
        if isinstance(self._n_channels, dict):
            return int(self._n_channels[subject])
        return int(self._n_channels)

    def _classification_raw(self, rng, n_ch):
        sf = self.sfreq
        names = list(self.event_id)
        n_cls = len(names)
        order = np.repeat(np.arange(n_cls), self.n_trials_per_class)
        if self.cue_order == "interleaved":
            rng.shuffle(order)
        trial_n = int(self.trial_duration * sf)
        isi_n = int(self.isi * sf)
        n_times = isi_n + len(order) * (trial_n + isi_n)
        data = self._noise(rng, n_ch, n_times)
        codes = np.zeros(n_times, dtype=int)
        t = np.arange(trial_n) / sf
        chans_per_class = max(1, n_ch // n_cls)
        pos = isi_n
        for k in order:
            codes[pos : pos + trial_n] = self.event_id[names[k]]
            chans = slice(k * chans_per_class, (k + 1) * chans_per_class)
            phase = rng.uniform(0, 2 * np.pi)
            burst = self.snr * np.sin(2 * np.pi * self.class_freqs[k] * t + phase)
            data[chans, pos : pos + trial_n] += burst
            pos += trial_n + isi_n
        data *= 1e-5  # volts
        ch_names = [f"E{i + 1:03d}" for i in range(n_ch)] + ["STI"]
        ch_types = ["ecog"] * n_ch + ["stim"]
        info = mne.create_info(ch_names, sf, ch_types)
        raw = mne.io.RawArray(np.vstack([data, codes[None, :]]), info, verbose=False)
        raw.set_annotations(
            annotations_from_codes(codes, sf, {v: k for k, v in self.event_id.items()})
        )
        return raw

    def _regression_raw(self, rng, n_ch):
        sf = self.sfreq
        n_times = int(self.duration * sf)
        t = np.arange(n_times) / sf
        # smooth targets: low-pass filtered noise, ~1 Hz bandwidth
        targets = rng.standard_normal((self.n_targets, n_times))
        kernel = np.exp(-0.5 * (np.arange(-int(sf), int(sf) + 1) / (0.25 * sf)) ** 2)
        kernel /= kernel.sum()
        targets = np.stack([np.convolve(x, kernel, mode="same") for x in targets])
        targets /= targets.std(axis=1, keepdims=True)
        data = self._noise(rng, n_ch, n_times)
        carrier = np.sin(2 * np.pi * 70.0 * t)
        for ch in range(n_ch):
            k = ch % self.n_targets
            data[ch] += self.snr * (1.0 + 0.8 * np.tanh(targets[k])) * carrier
        data *= 1e-5
        if self.n_targets == 5:
            tnames = [f"flex_{f}" for f in FINGERS]
        elif self.n_targets == 2:
            tnames = ["CursorPosX", "CursorPosY"]
        else:
            tnames = [f"target_{i}" for i in range(self.n_targets)]
        ch_names = [f"E{i + 1:03d}" for i in range(n_ch)] + tnames
        ch_types = ["ecog"] * n_ch + ["misc"] * self.n_targets
        info = mne.create_info(ch_names, sf, ch_types)
        return mne.io.RawArray(np.vstack([data, targets]), info, verbose=False)

    # -- API -------------------------------------------------------------------
    def _get_single_subject_data(self, subject):
        out = {}
        for session in range(self.n_sessions):
            out[str(session)] = {}
            for run in range(self.n_runs):
                rng = self._rng(subject, session, run)
                n_ch = self._n_ch(subject)
                if self.is_regression:
                    raw = self._regression_raw(rng, n_ch)
                else:
                    raw = self._classification_raw(rng, n_ch)
                raw.info["description"] = f"FakeECoG/{subject}/{session}/{run}"
                out[str(session)][str(run)] = raw
        return out

    def data_path(self, subject):
        return []

    def get_electrode_info(self, subject):
        n = self._n_ch(subject)
        cols = int(np.ceil(np.sqrt(n)))
        idx = np.arange(n)
        pos = np.stack([10.0 * (idx % cols), 10.0 * (idx // cols), np.zeros(n)], axis=1)
        return ElectrodeInfo(
            positions=pos,
            labels=[f"E{i + 1:03d}" for i in range(n)],
            coord_frame="mni",
            grid_type="grid",
            spacing_mm=10.0,
        )
