"""Registry tests: no data download needed."""

import numpy as np
import pytest

from moecog.datasets import EXPERIMENTS, MillerLibrary, annotations_from_codes
from moecog.datasets.miller_library import (
    _FACES_MAP,
    _grasp_map,
    _visual_search_map,
)

# subjects per experiment from Miller (2019) and the 2026-09-09 inventory
EXPECTED_SUBJECTS = {
    "fingerflex": 9, "joystick_track": 4, "mouse_track": 4, "motor_basic": 19,
    "imagery_basic": 7, "imagery_feedback": 4, "gestures": 5, "faces_basic": 14,
    "faces_noise": 7, "memory_nback": 4, "visual_search": 5, "speech_basic": 7,
    "speech_lists": 3, "fixation_PAC": 10, "fixation_pwrlaw": 20, "fixation_highfreq": 4,
}


def test_registry_counts():
    assert set(EXPERIMENTS) == set(EXPECTED_SUBJECTS)
    for name, n in EXPECTED_SUBJECTS.items():
        assert len(EXPERIMENTS[name].subjects) == n, name
    n_files = sum(len(r) for spec in EXPERIMENTS.values() for r in spec.runs.values())
    assert n_files == 204  # "204 individual datasets" (Miller 2019)
    patients = {s for spec in EXPERIMENTS.values() for s in spec.subjects}
    assert len(patients) == 36  # 34 in the patient table + gw, h0 (fixation_pwrlaw only)


def test_event_ids_unique_per_name():
    for spec in EXPERIMENTS.values():
        ev = spec.event_id
        if ev is None:
            continue
        assert len(set(ev.values())) == len(ev), spec.name
        assert all(v >= 1 for v in ev.values())


def test_dataset_object_without_data():
    ds = MillerLibrary("imagery_basic", root="/nonexistent", download=False)
    assert ds.subject_list == ["bp", "fp", "hh", "jc", "jm", "rh", "rr"]
    assert ds.n_sessions == 2
    assert ds.event_id == {"tongue": 1, "hand": 2}
    assert ds.interval == [0.0, 3.0]
    with pytest.raises(FileNotFoundError):
        ds.data_path("bp")
    rest = MillerLibrary("motor_basic", root="/nonexistent", download=False, include_rest=True)
    assert rest.event_id["rest"] == 0
    with pytest.raises(ValueError):
        MillerLibrary("no_such_experiment")


def test_annotations_from_codes():
    codes = np.array([0, 0, 11, 11, 11, 0, 12, 12, 0, 7])
    ann = annotations_from_codes(codes, 10.0, {11: "tongue", 12: "hand"})
    assert list(ann.description) == ["tongue", "hand", "code_7"]
    np.testing.assert_allclose(ann.onset, [0.2, 0.6, 0.9])
    np.testing.assert_allclose(ann.duration, [0.3, 0.2, 0.1])
    with_rest = annotations_from_codes(codes, 10.0, {11: "tongue", 12: "hand"}, include_rest=True)
    assert list(with_rest.description).count("rest") == 3


def test_code_maps():
    faces = np.array([0, 1, 50, 51, 100, 101])
    np.testing.assert_array_equal(_FACES_MAP(faces, {}), [0, 1, 1, 2, 2, 0])
    vis = np.array([0, 1, 10, 11, 21, 31, 40, 41])
    np.testing.assert_array_equal(_visual_search_map(vis, {}), [0, 1, 1, 2, 3, 4, 4, 0])
    grasp = np.arange(10)
    np.testing.assert_array_equal(_grasp_map(grasp, {}), [0, 1, 2, 3, 4, 5, 6, 7, 6, 7])
