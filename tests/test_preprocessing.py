import mne
import numpy as np
import pytest

from moecog.paradigms import MotorClassification
from moecog.preprocessing import (
    CommonAverageReference,
    HilbertEnvelope,
    NotchFilter,
    apply_raw_steps,
    chang_high_gamma,
)


def _raw(sfreq=500.0, n_ch=4, seconds=4.0, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(int(sfreq * seconds)) / sfreq
    data = rng.standard_normal((n_ch, len(t))) * 1e-5
    data += 5e-5 * np.sin(2 * np.pi * 60 * t)  # shared line noise
    info = mne.create_info([f"E{i}" for i in range(n_ch)] + ["STI"], sfreq,
                           ["ecog"] * n_ch + ["stim"])
    return mne.io.RawArray(np.vstack([data, np.zeros(len(t))]), info, verbose=False)


def test_car_removes_common_signal():
    raw = _raw()
    before = raw.get_data(picks="ecog")
    out = apply_raw_steps(raw, [CommonAverageReference()])
    after = out.get_data(picks="ecog")
    assert np.abs(after.mean(axis=0)).max() < 1e-12
    assert not np.allclose(before, after)
    # groups: two blocks referenced separately
    raw2 = _raw()
    CommonAverageReference(groups=[["E0", "E1"], ["E2", "E3"]]).apply(raw2)
    d = raw2.get_data(picks="ecog")
    assert np.abs(d[:2].mean(axis=0)).max() < 1e-12


def test_notch_attenuates_line_noise():
    raw = _raw()
    psd_before = raw.compute_psd(picks="ecog", fmin=55, fmax=65, verbose=False).get_data().mean()
    NotchFilter(freqs=(60.0,)).apply(raw)
    psd_after = raw.compute_psd(picks="ecog", fmin=55, fmax=65, verbose=False).get_data().mean()
    assert psd_after < psd_before / 10


def test_hilbert_envelope_shapes_and_sensitivity():
    sf = 500.0
    t = np.arange(int(sf)) / sf
    X = np.random.default_rng(1).standard_normal((3, 2, len(t))) * 0.1
    X[0, 0] += np.sin(2 * np.pi * 100 * t)
    env = HilbertEnvelope(bands={"hg": (70, 150), "beta": (13, 30)}, sfreq=sf)
    F = env.fit_transform(X)
    assert F.shape == (3, 4, len(t))
    Fa = HilbertEnvelope(bands={"hg": (70, 150)}, sfreq=sf, average=True).fit_transform(X)
    assert Fa.shape == (3, 2) and Fa[0, 0] > Fa[1:, 0].max() + 1.0
    Fd = HilbertEnvelope(bands={"hg": (70, 150)}, sfreq=sf, decimate=5).fit_transform(X)
    assert Fd.shape[-1] == len(t) // 5
    Fz = HilbertEnvelope(bands={"hg": (70, 150)}, sfreq=sf, average=True, zscore=True)
    Fz.fit(X)
    assert np.allclose(Fz.transform(X).mean(axis=0), 0, atol=1e-8)


def test_chang_high_gamma_preset():
    sf = 1000.0
    X = np.random.default_rng(2).standard_normal((6, 3, 1000)) * 0.1
    tr = chang_high_gamma(sfreq=sf, average=True)
    F = tr.fit_transform(X)
    assert F.shape == (6, 3)
    assert np.allclose(F.mean(axis=0), 0, atol=1e-8)


def test_paradigm_raw_steps(fake_cls):
    paradigm = MotorClassification(fmin=1.0, fmax=100.0, tmax=1.0,
                                   raw_steps=[CommonAverageReference(), NotchFilter((60.0,))])
    X, y, meta = paradigm.get_data(fake_cls, subjects=[1])
    plain = MotorClassification(fmin=1.0, fmax=100.0, tmax=1.0).get_data(fake_cls, subjects=[1])[0]
    assert X.shape == plain.shape and not np.allclose(X, plain)
    with pytest.raises(NotImplementedError):
        from moecog.preprocessing import RawStep

        RawStep().apply(None)
