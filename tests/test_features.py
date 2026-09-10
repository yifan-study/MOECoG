import numpy as np

from moecog.pipelines.features import HighGammaPower, LogBandPower


def test_log_band_power_shape_and_sensitivity():
    rng = np.random.default_rng(0)
    sf = 500.0
    t = np.arange(int(sf)) / sf
    X = rng.standard_normal((4, 3, len(t))) * 0.1
    X[0, 0] += np.sin(2 * np.pi * 100 * t)  # high-gamma in sample 0, channel 0
    F = LogBandPower(sfreq=sf).fit_transform(X)
    assert F.shape == (4, 3 * 4)
    hg = F.reshape(4, 3, 4)[:, 0, 3]
    assert hg[0] > hg[1:].max() + 1.0


def test_bands_above_nyquist_dropped():
    X = np.random.default_rng(1).standard_normal((2, 2, 100))
    F = LogBandPower(sfreq=100.0).fit_transform(X)
    assert F.shape == (2, 2 * 3)  # high_gamma (70-150) dropped at 100 Hz
    assert HighGammaPower(sfreq=1000.0).fit_transform(np.ones((1, 1, 300))).shape == (1, 1)
