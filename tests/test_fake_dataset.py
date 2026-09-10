import mne
import numpy as np

from moecog.datasets import FakeECoGDataset


def test_classification_raw_has_annotations(fake_cls):
    data = fake_cls.get_data(subjects=[1])
    raw = data[1]["0"]["0"]
    assert raw.info["sfreq"] == 250.0
    assert len(mne.pick_types(raw.info, ecog=True)) == 8
    assert "STI" in raw.ch_names
    descs = list(raw.annotations.description)
    assert descs.count("hand") == 12 and descs.count("tongue") == 12


def test_deterministic():
    a = FakeECoGDataset(seed=5).get_data(subjects=[1])[1]["0"]["0"].get_data()
    b = FakeECoGDataset(seed=5).get_data(subjects=[1])[1]["0"]["0"].get_data()
    np.testing.assert_array_equal(a, b)


def test_regression_raw_targets(fake_reg):
    raw = fake_reg.get_data(subjects=[1])[1]["0"]["0"]
    assert [c for c in raw.ch_names if c.startswith("flex_")] == [
        "flex_thumb", "flex_index", "flex_middle", "flex_ring", "flex_little"]
    assert raw.get_data(picks="misc").shape[0] == 5


def test_electrode_info(fake_cls):
    info = fake_cls.get_electrode_info(1)
    assert info.positions.shape == (8, 3)
    assert info.coord_frame == "mni"


def test_unknown_subject_raises(fake_cls):
    import pytest

    with pytest.raises(ValueError):
        fake_cls.get_data(subjects=[99])
