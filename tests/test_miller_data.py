"""Tests against the real library; run with MOECOG_MILLER_DIR=<root> -m slow."""

import mne
import numpy as np
import pytest
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from moecog.datasets import EXPERIMENTS, MillerLibrary
from moecog.evaluations import WithinSubjectCV
from moecog.paradigms import FaceHouseClassification, FingerFlexionRegression, MotorClassification
from moecog.pipelines.features import HighGammaPower

from .conftest import miller_root, needs_miller

pytestmark = [pytest.mark.slow, needs_miller]


def _ds(experiment, **kw):
    return MillerLibrary(experiment, root=miller_root(), download=False, **kw)


def test_every_registered_file_exists():
    missing = []
    for name, spec in EXPERIMENTS.items():
        ds = _ds(name)
        for subject in ds.subject_list:
            try:
                ds.data_path(subject)
            except FileNotFoundError as e:
                missing.append(str(e))
    assert not missing, "\n".join(missing)


def test_motor_basic_bp():
    ds = _ds("motor_basic")
    raw = ds.get_data(subjects=["bp"])["bp"]["0"]["mot_t_h"]
    assert raw.info["sfreq"] == 1000.0
    assert len(mne.pick_types(raw.info, ecog=True)) == 47
    descs = list(raw.annotations.description)
    assert descs.count("hand") == 30 and descs.count("tongue") == 30
    assert np.allclose(raw.annotations.duration, 3.0)
    einfo = ds.get_electrode_info("bp")
    assert einfo.positions.shape == (47, 3) and einfo.coord_frame == "talairach"


def test_motor_classification_above_chance():
    ds = _ds("motor_basic")
    paradigm = MotorClassification(fmin=1.0, fmax=200.0, tmax=3.0)
    pipes = {"hg+lda": make_pipeline(HighGammaPower(sfreq=1000.0), StandardScaler(),
                                     LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto"))}
    res = WithinSubjectCV(paradigm, [ds], n_splits=5).process(pipes, subjects=["bp"])
    acc = res[res["metric"] == "accuracy"]["score"].mean()
    assert acc > 0.7, acc


def test_faces_basic_wc():
    ds = _ds("faces_basic")
    raw = ds.get_data(subjects=["wc"])["wc"]["faceshouses"]["0"]
    descs = list(raw.annotations.description)
    assert descs.count("face") == 150 and descs.count("house") == 150
    X, y, meta = FaceHouseClassification(fmax=200.0).get_data(ds, subjects=["wc"])
    assert X.shape[0] == 300 and X.shape[2] == 401
    einfo = ds.get_electrode_info("wc")
    assert einfo.coord_frame == "voxel" and einfo.region_code is not None


def test_faces_noise_coherence_channel():
    ds = _ds("faces_noise")
    raw = ds.get_data(subjects=["ap"])["ap"]["fhnoisy"]["0"]
    coh = raw.get_data(picks=["coherence"])[0]
    assert np.nanmax(coh) == 100.0 and np.nanmin(coh) == 0.0
    assert len(raw.annotations) == 630


def test_gestures_grasp_and_imagery_feedback():
    g = _ds("gestures").get_data(subjects=["de"])["de"]
    descs = list(g["glovefingersgrasp"]["0"].annotations.description)
    assert descs.count("pinch") == 40 and descs.count("fist") == 40
    assert "dg_thumb" in g["glovefingersgrasp"]["0"].ch_names
    fb = _ds("imagery_feedback").get_data(subjects=["fp"])["fp"]
    assert set(fb) == {"fbLR_hand", "fbUD_tongue", "im_t_h", "mot_t_h"}
    assert "cursor" in fb["fbLR_hand"]["0"].ch_names


def test_fingerflex_regression_windows():
    ds = _ds("fingerflex")
    paradigm = FingerFlexionRegression(window_size=0.5, window_stride=0.5)
    X, y, meta = paradigm.get_data(ds, subjects=["mv"])
    assert y.shape[1] == 5 and X.shape[1] == len(mne.pick_types(
        ds.get_data(subjects=["mv"])["mv"]["0"]["fingerflex"].info, ecog=True))
    assert ds.get_electrode_info("mv").region_code is not None
