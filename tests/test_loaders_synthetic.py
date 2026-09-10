"""Loader tests on synthetic files (no downloads)."""

import pickle
import sys
import types

import mne
import numpy as np
import pytest

from moecog.datasets.nwb import read_nwb_raw
from moecog.paradigms import EpochedClassification


def _write_nwb(path, n_ch=4, sfreq=200.0, seconds=6.0):
    from datetime import datetime, timezone

    from pynwb import NWBHDF5IO, NWBFile
    from pynwb.ecephys import ElectricalSeries

    nwb = NWBFile(session_description="synthetic", identifier="syn1",
                  session_start_time=datetime(2026, 1, 1, tzinfo=timezone.utc))
    dev = nwb.create_device(name="grid")
    grp = nwb.create_electrode_group(name="grid1", description="g", location="motor", device=dev)
    for i in range(n_ch):
        nwb.add_electrode(x=float(i), y=0.0, z=0.0, location="motor", group=grp, id=i)
    region = nwb.create_electrode_table_region(list(range(n_ch)), "all")
    data = np.random.default_rng(0).standard_normal((int(seconds * sfreq), n_ch)) * 1e-5
    es = ElectricalSeries(name="ECoG", data=data, electrodes=region, rate=sfreq, starting_time=0.0)
    nwb.add_acquisition(es)
    nwb.add_trial_column(name="cue", description="cue")
    for k in range(5):
        nwb.add_trial(start_time=0.5 + k, stop_time=1.0 + k, cue="hand" if k % 2 else "tongue")
    with NWBHDF5IO(str(path), "w") as io:
        io.write(nwb)


def test_read_nwb_raw_and_trials(tmp_path):
    path = tmp_path / "syn.nwb"
    _write_nwb(path)
    raw, meta, einfo = read_nwb_raw(path)
    assert raw.info["sfreq"] == 200.0 and len(raw.ch_names) == 4
    assert meta["series"] == "ECoG" and meta["n_annotations"] == 5
    assert sorted(set(raw.annotations.description)) == ["trials/hand", "trials/tongue"]
    assert einfo is not None and einfo.positions.shape == (4, 3)
    raw2, meta2, _ = read_nwb_raw(path, max_seconds=2.0)
    assert raw2.n_times == 400 and meta2["n_annotations"] == 2


def test_epochs_dataset_through_paradigm():
    """A dataset delivering mne.Epochs (figshare/bbci style) works with the epoched paradigm."""
    from moecog.datasets.base import BaseECoGDataset

    sf, n = 100.0, 30
    rng = np.random.default_rng(1)
    X = rng.standard_normal((n, 3, 100)) * 1e-5
    y = np.array([1, 2] * (n // 2))
    events = np.column_stack([np.arange(n) * 100, np.zeros(n, int), y])
    info = mne.create_info(["a", "b", "c"], sf, ["ecog"] * 3)
    epochs = mne.EpochsArray(X, info, events=events, event_id={"rest": 1, "move": 2}, tmin=0.0, verbose=False)

    class Ep(BaseECoGDataset):
        def __init__(self):
            super().__init__([1], 1, {"rest": 1, "move": 2}, "Ep", "naturalistic", [0.0, 1.0], sf)

        def _get_single_subject_data(self, subject):
            return {"0": {"0": epochs}}

        def data_path(self, subject):
            return []

        def get_electrode_info(self, subject):
            raise FileNotFoundError

    ds = Ep()
    par = EpochedClassification(tmin=0.0, tmax=0.5, fmin=1.0, fmax=40.0)
    Xo, yo, meta = par.get_data(ds)
    assert Xo.shape == (n, 3, 51) and set(yo) == {"rest", "move"}
    only = EpochedClassification(events=["move"], fmin=1.0, fmax=40.0, min_classes=1)
    assert only.get_data(ds)[0].shape[0] == n // 2


def test_duin_pickle_shim(tmp_path):
    """Du-IN files pickle a utils.DotDict; the loader must unpickle them without that module."""
    from moecog.datasets.misc import DuIN

    mod = types.ModuleType("utils")

    class DotDict(dict):
        pass

    mod.DotDict = DotDict
    sys.modules["utils"] = mod
    try:
        info = DotDict(ch_names=["A1", "A2"], sfreq=100.0)
        trials = [DotDict(name="word%d" % (k % 2), data_s=np.random.default_rng(k).standard_normal((2, 100)))
                  for k in range(6)]
        (tmp_path / "001_run1_info").write_bytes(pickle.dumps(info))
        (tmp_path / "001_run1_data").write_bytes(pickle.dumps(trials))
    finally:
        del sys.modules["utils"]
    ds = DuIN(subjects=["001"], runs=[1], root=tmp_path)
    ds.data_path = lambda subject: [tmp_path / "001_run1_data", tmp_path / "001_run1_info"]
    data = ds.get_data(subjects=["001"])["001"]["0"]["run1"]
    assert isinstance(data, mne.BaseEpochs) and len(data) == 6 and set(ds.event_id) == {"word0", "word1"}


def test_peterson_moverest_netcdf(tmp_path):
    xr = pytest.importorskip("xarray")
    from moecog.datasets.misc import PetersonMoveRest

    t = np.arange(-2.0, 2.0, 0.004)
    arr = np.random.default_rng(2).standard_normal((8, 5, len(t)))
    arr[:, -1, :] = np.repeat([0, 1], 4)[:, None]
    da = xr.DataArray(arr, dims=("events", "channels", "time"),
                      coords={"events": np.arange(8), "channels": np.arange(5), "time": t})
    da.to_netcdf(tmp_path / "EC09_ecog_data.nc")
    ds = PetersonMoveRest(subjects=["EC09"], root=tmp_path)
    ep = ds.get_data(subjects=["EC09"])["EC09"]["0"]["0"]
    assert isinstance(ep, mne.BaseEpochs) and ep.info["sfreq"] == 250.0 and len(ep) == 8
    assert sorted(ep.event_id) == ["move", "rest"] and ep.get_data().shape[1] == 4
