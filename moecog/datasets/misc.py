"""Loaders for datasets with their own formats (figshare, OSF, Dataverse, HF, bbci).

Each class downloads the files it needs into ``$MOECOG_DATA_DIR/<source>/...``
and exposes the MOECoG interface. Formats were inspected on 2026-09-09; see
``docs/dataset_catalog.md`` for provenance.
"""

from __future__ import annotations

import gzip
import io
import os
import pickle
import re
import shutil
import urllib.request
import warnings
import zipfile
from pathlib import Path

import mne
import numpy as np

from .base import BaseECoGDataset


def _data_dir() -> Path:
    from ..utils import get_data_dir

    return get_data_dir()


def _download(url: str, dest: Path, expected_size=None, retries: int = 3) -> Path:
    """Stream ``url`` to ``dest`` with HTTP-range resumption.

    A file that already exists is trusted unless ``expected_size`` disagrees with it. Interrupted transfers
    are written to ``dest.part`` and resumed with a ``Range`` request, so multi-GB archives (OSF, Hugging
    Face, figshare) survive dropped connections; servers that ignore ranges restart from zero.
    """
    dest = Path(dest)
    if dest.is_file() and (expected_size is None or dest.stat().st_size == expected_size):
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    last_err = None
    for attempt in range(retries):
        offset = part.stat().st_size if part.is_file() else 0
        headers = {"User-Agent": "moecog/0.2"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                resumed = offset and resp.status == 206
                total = resp.headers.get("Content-Length")
                total = int(total) + (offset if resumed else 0) if total else None
                with open(part, "ab" if resumed else "wb") as fh:
                    shutil.copyfileobj(resp, fh, length=1 << 22)
            size = part.stat().st_size
            if (total is not None and size != total) or (expected_size is not None and size != expected_size):
                last_err = OSError(f"{url}: got {size} bytes, expected {expected_size or total}")
                if total is not None and size < total:
                    continue  # short read: resume on the next attempt
                part.unlink(missing_ok=True)
                continue
            part.replace(dest)
            return dest
        except (OSError, EOFError) as err:  # includes URLError, IncompleteRead, timeouts
            last_err = err
    raise OSError(f"download of {url} failed after {retries} attempts: {last_err}")


def _raw_from_array(data, sfreq, ch_names=None, ch_types=None, annotations=None, description=""):
    n_ch = data.shape[0]
    ch_names = ch_names or [f"E{i + 1:03d}" for i in range(n_ch)]
    ch_types = ch_types or ["ecog"] * n_ch
    info = mne.create_info(ch_names, sfreq, ch_types)
    raw = mne.io.RawArray(np.asarray(data, dtype=float), info, verbose=False)
    if annotations is not None:
        raw.set_annotations(annotations)
    raw.info["description"] = description
    return raw


class _SimpleDataset(BaseECoGDataset):
    """Datasets whose subjects map to one Raw (or Epochs) each."""

    def data_path(self, subject):
        return []

    def get_electrode_info(self, subject):
        raise FileNotFoundError(f"No electrode coordinates distributed with {self.code}")


# ------------------------------------------------------------------ BCI competitions
class BCICompIV4(_SimpleDataset):
    """BCI Competition IV dataset 4 (finger flexion, 3 subjects).

    Reads ``sub<k>_comp.mat`` (+ ``sub<k>_testlabels.mat``) from the folder of
    the Miller SDR deposit (``BCI_Competion4_dataset4_data_fingerflexions``)
    under ``$MOECOG_MILLER_DIR`` or ``root``. The competition split is kept as
    annotations ``train``/``test`` on one continuous recording.
    """

    def __init__(self, root=None):
        root = Path(root).expanduser() if root else None
        if root is None:
            base = os.environ.get("MOECOG_MILLER_DIR")
            root = Path(base) / "BCI_Competion4_dataset4_data_fingerflexions" if base else None
        self.root = root
        subs = [1, 2, 3]
        super().__init__(subjects=subs, sessions_per_subject=1, events=None, code="BCICompIV-4",
                         paradigm="motor_regression", interval=None, sfreq=1000.0,
                         doi="10.1088/1741-2560/6/6/066001")

    def data_path(self, subject):
        if self.root is None or not self.root.is_dir():
            raise FileNotFoundError("BCI-IV-4 folder not found; set MOECOG_MILLER_DIR or root")
        files = sorted(self.root.rglob(f"sub{subject}_comp.mat"))
        if not files:
            raise FileNotFoundError(f"sub{subject}_comp.mat not under {self.root}")
        return files

    def _get_single_subject_data(self, subject):
        import scipy.io as sio

        path = self.data_path(subject)[0]
        m = sio.loadmat(path)
        train = np.asarray(m["train_data"], dtype=float).T
        test = np.asarray(m["test_data"], dtype=float).T
        dg_tr = np.asarray(m["train_dg"], dtype=float).T
        lab = sorted(path.parent.rglob(f"sub{subject}_testlabels.mat"))
        dg_te = np.asarray(sio.loadmat(lab[0])["test_dg"], dtype=float).T if lab else np.zeros((5, test.shape[1]))
        data = np.concatenate([train, test], axis=1) * 1e-6
        dg = np.concatenate([dg_tr, dg_te], axis=1)
        fingers = ["thumb", "index", "middle", "ring", "little"]
        n_ch = data.shape[0]
        raw = _raw_from_array(np.vstack([data, dg]), 1000.0,
                              [f"E{i + 1:03d}" for i in range(n_ch)] + [f"flex_{f}" for f in fingers],
                              ["ecog"] * n_ch + ["misc"] * 5, description=f"BCI-IV-4 sub{subject}")
        raw.set_annotations(mne.Annotations([0.0, train.shape[1] / 1000.0],
                                            [train.shape[1] / 1000.0, test.shape[1] / 1000.0],
                                            ["train", "test"]))
        return {"0": {"0": raw}}


class BCICompIII1(_SimpleDataset):
    """BCI Competition III dataset I (Tübingen ECoG motor imagery, 1 subject, 8x8 grid).

    Downloads ``Competition_train.mat.gz`` (278 trials, 3 s at 1 kHz, labels
    -1 pinky / 1 tongue) and, if reachable, ``Competition_test.mat.gz``; the
    test labels were published separately and are not attached here.
    """

    URL = "https://www.bbci.de/competition/download/competition_iii/tuebingen/"

    def __init__(self, root=None):
        self.root = Path(root).expanduser() if root else _data_dir() / "bbci" / "bci_iii_1"
        super().__init__(subjects=[1], sessions_per_subject=2, events={"pinky": 1, "tongue": 2},
                         code="BCICompIII-1", paradigm="motor_imagery", interval=[0.0, 3.0],
                         sfreq=1000.0, doi="10.1109/TBME.2004.826692")

    def data_path(self, subject):
        return [_download(self.URL + "Competition_train.mat.gz", self.root / "Competition_train.mat.gz")]

    def _get_single_subject_data(self, subject):
        import scipy.io as sio

        path = self.data_path(subject)[0]
        with gzip.open(path, "rb") as fh:
            m = sio.loadmat(io.BytesIO(fh.read()))
        X = np.asarray(m["X"], dtype=float) * 1e-6  # (trials, ch, times)
        y = np.asarray(m["Y"]).ravel().astype(int)
        n_trials, n_ch, n_t = X.shape
        events = np.column_stack([np.arange(n_trials) * n_t, np.zeros(n_trials, int),
                                  np.where(y < 0, 1, 2)])
        info = mne.create_info([f"E{i + 1:03d}" for i in range(n_ch)], 1000.0, ["ecog"] * n_ch)
        epochs = mne.EpochsArray(X, info, events=events, event_id={"pinky": 1, "tongue": 2},
                                 tmin=0.0, verbose=False)
        return {"train": {"0": epochs}}


# ------------------------------------------------------------------ figshare (Peterson, Rogers)
_PETERSON = {
    "moverest": {"EC01": 24790064, "EC11": 24790208, "EC10": 24790205, "EC09": 24790202},
    "pose": {"EC01": 30725915, "EC02": 30725987, "EC03": 30725996, "EC04": 30726020},
    "reach": {"01": 22279917},
}


def _figshare_url(file_id):
    return f"https://ndownloader.figshare.com/files/{file_id}"


class PetersonMoveRest(_SimpleDataset):
    """Peterson 2021 naturalistic move-vs-rest events (figshare 13010546, xarray .nc).

    Each file holds events x channels x time with the label in the last
    "electrode"; loaded as ``mne.EpochsArray`` with classes ``move``/``rest``.
    """

    def __init__(self, subjects=("EC09",), root=None):
        self.root = Path(root).expanduser() if root else _data_dir() / "figshare" / "peterson_moverest"
        super().__init__(subjects=list(subjects), sessions_per_subject=1,
                         events={"rest": 1, "move": 2}, code="Peterson2021-moverest",
                         paradigm="naturalistic", interval=[0.0, 1.0], sfreq=float("nan"))

    def data_path(self, subject):
        fid = _PETERSON["moverest"].get(subject)
        if fid is None:
            raise ValueError(f"{subject}: file id unknown (only {list(_PETERSON['moverest'])} mapped)")
        return [_download(_figshare_url(fid), self.root / f"{subject}_ecog_data.nc")]

    def _get_single_subject_data(self, subject):
        import xarray as xr

        ds = xr.open_dataset(self.data_path(subject)[0])
        var = list(ds.data_vars)[0]
        da = ds[var]
        arr = np.asarray(da.values, dtype=float)
        # dims are (events, channels, time) in the figshare description
        if arr.ndim != 3:
            raise ValueError(f"unexpected dims {da.dims}")
        lab = np.nanmedian(arr[:, -1, :], axis=1)
        vals = np.unique(lab[~np.isnan(lab)])
        if len(vals) == 2:
            labels = (lab == vals[1]).astype(float)  # higher value = move
        else:
            labels = (lab > np.nanmedian(lab)).astype(float)
        X = arr[:, :-1, :]
        times = np.asarray(da.coords[da.dims[-1]].values, dtype=float)
        sfreq = float(round(1.0 / np.median(np.diff(times)))) if len(times) > 1 else 500.0
        tmin = float(times[0]) if len(times) else 0.0
        y = np.where(labels > 0.5, 2, 1)
        events = np.column_stack([np.arange(len(y)) * X.shape[2], np.zeros(len(y), int), y])
        info = mne.create_info([f"E{i + 1:03d}" for i in range(X.shape[1])], sfreq, ["ecog"] * X.shape[1])
        epochs = mne.EpochsArray(X * 1e-6, info, events=events, event_id={"rest": 1, "move": 2},
                                 tmin=tmin, verbose=False)
        return {"0": {"0": epochs}}


class PetersonPose(PetersonMoveRest):
    """Peterson 2021 ECoG with 2-D arm positions (figshare 16599782)."""

    def __init__(self, subjects=("EC02",), root=None):
        BaseECoGDataset.__init__(self, subjects=list(subjects), sessions_per_subject=1, events=None,
                                 code="Peterson2021-pose", paradigm="naturalistic", interval=None,
                                 sfreq=float("nan"))
        self.root = Path(root).expanduser() if root else _data_dir() / "figshare" / "peterson_pose"

    def data_path(self, subject):
        fid = _PETERSON["pose"].get(subject)
        if fid is None:
            raise ValueError(f"{subject}: file id unknown")
        return [_download(_figshare_url(fid), self.root / f"{subject}_ecog_data.nc")]

    def _get_single_subject_data(self, subject):
        import xarray as xr

        ds = xr.open_dataset(self.data_path(subject)[0])
        var = list(ds.data_vars)[0]
        arr = np.asarray(ds[var].values, dtype=float)
        if arr.ndim != 3:
            raise ValueError(f"unexpected shape {arr.shape}")
        times = np.asarray(ds[var].coords[ds[var].dims[-1]].values, dtype=float)
        sfreq = float(round(1.0 / np.median(np.diff(times)))) if len(times) > 1 else 500.0
        info = mne.create_info([f"E{i + 1:03d}" for i in range(arr.shape[1])], sfreq, ["ecog"] * arr.shape[1])
        events = np.column_stack([np.arange(arr.shape[0]) * arr.shape[2], np.zeros(arr.shape[0], int),
                                  np.ones(arr.shape[0], int)])
        epochs = mne.EpochsArray(arr * 1e-6, info, events=events, event_id={"event": 1},
                                 tmin=float(times[0]) if len(times) else 0.0, verbose=False)
        return {"0": {"0": epochs}}


class PetersonReach(_SimpleDataset):
    """Peterson 2020 naturalistic reach epochs (figshare 12115728, MNE .fif)."""

    def __init__(self, subjects=("01",), root=None):
        self.root = Path(root).expanduser() if root else _data_dir() / "figshare" / "peterson_reach"
        super().__init__(subjects=list(subjects), sessions_per_subject=1, events=None,
                         code="Peterson2020-reach", paradigm="naturalistic", interval=None,
                         sfreq=float("nan"))

    def data_path(self, subject):
        fid = _PETERSON["reach"].get(subject)
        if fid is None:
            raise ValueError(f"{subject}: only subject 01 day 3 is mapped")
        return [_download(_figshare_url(fid), self.root / f"subj_{subject}_day_3_r_epo.fif")]

    def _get_single_subject_data(self, subject):
        epochs = mne.read_epochs(self.data_path(subject)[0], preload=True, verbose=False)
        types = {ch: "ecog" for ch, t in zip(epochs.ch_names, epochs.get_channel_types()) if t == "eeg"}
        if types:
            epochs.set_channel_types(types, verbose=False)
        self.event_id = dict(epochs.event_id)
        return {"day3": {"0": epochs}}


class RogersMicroECoG(_SimpleDataset):
    """Rogers 2019 submillimeter µECoG, unlabeled 2 s windows (figshare 7633418)."""

    FILES = {"S1": 14181143, "S2": 14181137, "M1": 14181167}

    def __init__(self, subjects=("S2",), root=None):
        self.root = Path(root).expanduser() if root else _data_dir() / "figshare" / "rogers_uecog"
        super().__init__(subjects=list(subjects), sessions_per_subject=1, events=None,
                         code="Rogers2019-uECoG", paradigm="rest", interval=None, sfreq=float("nan"))

    def data_path(self, subject):
        return [_download(_figshare_url(self.FILES[subject]), self.root / f"{subject}_data.mat")]

    def _get_single_subject_data(self, subject):
        path = self.data_path(subject)[0]
        arrays, sfreq = {}, 4000.0
        try:
            import scipy.io as sio

            m = sio.loadmat(path)
            arrays = {k: np.asarray(v) for k, v in m.items() if not k.startswith("__") and np.ndim(v) >= 2}
            for k in ("fs", "Fs", "srate", "sample_rate"):
                if k in m and np.size(m[k]) == 1:
                    sfreq = float(np.asarray(m[k]).ravel()[0])
        except (NotImplementedError, ValueError):
            import h5py

            with h5py.File(path, "r") as f:
                arrays = {k: np.asarray(f[k][()]) for k in f.keys() if isinstance(f[k], h5py.Dataset)}
                if "fs" in f:
                    sfreq = float(np.asarray(f["fs"][()]).ravel()[0])
        # MATLAB structs (dtype with field names): the windows live in a cell array 'epoch'
        flat, epochs_cell = {}, None
        for k, v in arrays.items():
            if v.dtype.names:
                el = v.flat[0]
                for name in v.dtype.names:
                    fv = np.asarray(el[name])
                    if name in ("fs", "fsds") and fv.size == 1:
                        sfreq = float(fv.ravel()[0])
                    if fv.dtype == object and fv.size > 1:
                        epochs_cell = fv
                    elif fv.dtype.kind in "fiu" and fv.size > 1000:
                        flat[f"{k}.{name}"] = fv
            elif v.dtype.kind in "fiu":
                flat[k] = v
        if epochs_cell is not None:
            wins = [np.asarray(w, dtype=float) for w in epochs_cell.ravel()]
            n_ch = min(w.shape[0] for w in wins)
            n_t = min(w.shape[1] for w in wins)
            X = np.stack([w[:n_ch, :n_t] for w in wins]) * 1e-6
            events = np.column_stack([np.arange(len(X)) * n_t, np.zeros(len(X), int), np.ones(len(X), int)])
            info = mne.create_info([f"E{i + 1:03d}" for i in range(n_ch)], sfreq, ["ecog"] * n_ch)
            epochs = mne.EpochsArray(X, info, events=events, event_id={"window": 1}, tmin=0.0, verbose=False)
            self.event_id = {"window": 1}
            return {"0": {"0": epochs}}
        arrays = flat
        big = max(arrays, key=lambda k: np.prod(arrays[k].shape))
        d = np.squeeze(np.asarray(arrays[big], dtype=float))
        if d.ndim == 3:  # (windows, ch, t) or (t, ch, windows)
            d = np.moveaxis(d, np.argmax(d.shape), 0)
            if d.shape[1] < d.shape[2]:
                d = d.reshape(-1, d.shape[-1]).T
            else:
                d = d.transpose(1, 0, 2).reshape(d.shape[1], -1)
        elif d.ndim == 2 and d.shape[0] > d.shape[1]:
            d = d.T
        raw = _raw_from_array(d * 1e-6, sfreq, description=f"Rogers µECoG {subject} ({big})")
        return {"0": {"0": raw}}


# ------------------------------------------------------------------ OSF (Verwoert iBIDS)
class VerwoertSpeech(_SimpleDataset):
    """Verwoert 2022 single-word production sEEG (OSF nrgx6, iBIDS zip with NWB files).

    The OSF project stores one file, ``SingleWordProductionDutch-iBIDS.zip`` (OSF guid ``g6q5m``, ~2.8 GB).
    It is fetched directly; the project-level ``?zip=`` endpoint wraps that zip in another zip whose
    single member carries the same file name, so extracting it in place truncates the archive being read.
    """

    ZIP = "https://osf.io/download/g6q5m/"
    ZIP_NAME = "verwoert_nrgx6_iBIDS.zip"

    def __init__(self, root=None, subjects=None, download=True):
        self.root = Path(root).expanduser() if root else _data_dir() / "osf" / "verwoert"
        self.download = download
        self._ensure()
        subs = sorted(p.name[4:] for p in (self.root / "SingleWordProductionDutch-iBIDS").glob("sub-*"))
        if subjects:
            subs = [s for s in subs if s in subjects]
        super().__init__(subjects=subs, sessions_per_subject=1, events=None, code="Verwoert2022-speech",
                         paradigm="speech", interval=[0.0, 1.0], sfreq=1024.0,
                         doi="10.1038/s41597-022-01542-9")

    def _ensure(self):
        d = self.root / "SingleWordProductionDutch-iBIDS"
        if d.is_dir():
            return
        if not self.download:
            raise FileNotFoundError(d)
        z = self.root / self.ZIP_NAME
        for attempt in range(2):
            z = _download(self.ZIP, z)
            if zipfile.is_zipfile(z):
                break
            z.unlink()  # truncated or an HTML error page: fetch again once
        else:
            raise OSError(f"{z} is not a valid zip archive after re-download")
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
            inner = [n for n in names if n.lower().endswith(".zip")]
            if len(names) == len(inner) + sum(n.endswith("/") for n in names) and inner:
                # wrapper archive (project-level export): unpack the real iBIDS zip it contains
                with zf.open(inner[0]) as src, open(self.root / "inner.zip", "wb") as dst:
                    shutil.copyfileobj(src, dst, length=1 << 22)
                with zipfile.ZipFile(self.root / "inner.zip") as zi:
                    zi.extractall(self.root)
                (self.root / "inner.zip").unlink()
            else:
                zf.extractall(self.root)
        if not d.is_dir():
            inner_dir = next(self.root.glob("*/SingleWordProductionDutch-iBIDS"), None)
            if inner_dir:
                shutil.move(str(inner_dir), str(d))

    def data_path(self, subject):
        d = self.root / "SingleWordProductionDutch-iBIDS" / f"sub-{subject}"
        return sorted(d.rglob("*.nwb"))

    def _get_single_subject_data(self, subject):
        from .nwb import read_nwb_raw

        out = {}
        for path in self.data_path(subject):
            raw, meta, einfo = read_nwb_raw(path, channel_types=("ecog", "seeg", "ieeg"))
            chans = list(path.parent.glob(f"sub-{subject}*_channels.tsv"))
            if chans and meta.get("series_type") == "TimeSeries":
                # the NWB carries no electrodes table: take names and types from the BIDS sidecar
                import pandas as pd

                cdf = pd.read_csv(chans[0], sep="\t")
                if len(cdf) == len(raw.ch_names) and "name" in cdf.columns:
                    names = [str(n) for n in cdf["name"]]
                    raw.rename_channels(dict(zip(raw.ch_names, names)))
                    if "type" in cdf.columns:
                        raw.set_channel_types({n: ("ecog" if str(t).upper() in ("ECOG", "SEEG", "IEEG") else "misc")
                                               for n, t in zip(names, cdf["type"])}, verbose=False)
            ev = list(path.parent.glob(f"sub-{subject}*_events.tsv"))
            if ev:
                import pandas as pd

                df = pd.read_csv(ev[0], sep="\t")
                col = "trial_type" if "trial_type" in df.columns else df.columns[-1]
                raw.set_annotations(mne.Annotations(df["onset"].astype(float), df["duration"].astype(float),
                                                    df[col].astype(str)))
            out.setdefault("0", {})[path.stem] = raw
            labels = sorted(set(raw.annotations.description))
            self.event_id = {lab: i + 1 for i, lab in enumerate(labels)} or None
        return out


# ------------------------------------------------------------------ Dataverse (Merk)
class MerkGripForce(_SimpleDataset):
    """Merk 2022 grip-force ECoG + STN (Harvard Dataverse IO2FLM).

    The deposit is a flat BIDS export (``.tab`` instead of ``.tsv``); this loader
    rebuilds ``sub-XXX/ses-YYY/ieeg/`` and reads BrainVision files with MNE.
    """

    ZIP = "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/IO2FLM"

    def __init__(self, root=None, subjects=None, download=True):
        self.root = Path(root).expanduser() if root else _data_dir() / "dataverse" / "merk"
        self.download = download
        self._ensure()
        subs = sorted({m.group(1) for f in (self.root / "bids").rglob("*_ieeg.vhdr")
                       for m in [re.search(r"sub-([A-Za-z0-9]+)", f.name)] if m})
        if subjects:
            subs = [s for s in subs if s in subjects]
        super().__init__(subjects=subs, sessions_per_subject=2, events=None, code="Merk2022-gripforce",
                         paradigm="motor_regression", interval=None, sfreq=float("nan"),
                         doi="10.7554/eLife.75126")

    def _ensure(self):
        bids = self.root / "bids"
        if bids.is_dir():
            return
        if not self.download:
            raise FileNotFoundError(bids)
        z = _download(self.ZIP, self.root / "merk_all.zip")
        flat = self.root / "flat"
        with zipfile.ZipFile(z) as zf:
            zf.extractall(flat)
        bids.mkdir(exist_ok=True)
        for f in flat.rglob("*"):
            if not f.is_file():
                continue
            name = f.name[:-4] + ".tsv" if f.name.endswith(".tab") else f.name
            m = re.match(r"sub-([A-Za-z0-9]+)(?:_ses-([A-Za-z0-9]+))?", name)
            if m:
                dest = bids / f"sub-{m.group(1)}"
                if m.group(2):
                    dest = dest / f"ses-{m.group(2)}"
                if any(k in name for k in ("_ieeg", "_channels", "_electrodes", "_coordsystem", "_events")):
                    dest = dest / "ieeg"
            else:
                dest = bids
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest / name)

    def data_path(self, subject):
        return sorted((self.root / "bids" / f"sub-{subject}").rglob("*_ieeg.vhdr"))

    def _get_single_subject_data(self, subject):
        out = {}
        for vhdr in self.data_path(subject):
            raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose=False)
            types = {}
            for ch in raw.ch_names:
                u = ch.upper()
                aux = any(k in u for k in ("STN", "LFP", "ANALOG", "FORCE", "EMG", "ACC", "ROT"))
                types[ch] = "misc" if (aux and "ECOG" not in u) else "ecog"
            raw.set_channel_types(types, verbose=False)
            m = re.search(r"ses-([A-Za-z0-9]+)", vhdr.name)
            r = re.search(r"run-([A-Za-z0-9]+)", vhdr.name)
            out.setdefault(m.group(1) if m else "0", {})[r.group(1) if r else "0"] = raw
        return out


def _load_hdf5_plugins():
    """Register third-party HDF5 filters (Blosc, LZ4, Zstd) when ``hdf5plugin`` is installed.

    The SWEC-ETHZ HDF5 exports are Blosc-compressed (filter id 32001); stock h5py wheels cannot decode them and
    fail with "Can't synchronously read data (can't open directory .../hdf5/lib/plugin)". Importing
    ``hdf5plugin`` registers the filters process-wide, so this is a no-op after the first call.
    """
    try:
        import hdf5plugin  # noqa: F401
    except ImportError:
        warnings.warn("hdf5plugin is not installed; Blosc/LZ4/Zstd-compressed HDF5 files (e.g. SWEC) will not "
                      "load. Install it with `pip install hdf5plugin`.", stacklevel=2)


# ------------------------------------------------------------------ Hugging Face
_HF = "https://huggingface.co/datasets/{repo}/resolve/main/{path}"


class _DotDict(dict):
    """Shim for the ``utils.DotDict`` class pickled in Du-IN files."""

    __getattr__ = dict.get

    def __setstate__(self, state):
        self.update(state or {})


class DuIN(_SimpleDataset):
    """Du-IN Mandarin word-recitation sEEG (HF liulab-repository/Du-IN, CC-BY-4.0)."""

    REPO = "liulab-repository/Du-IN"

    def __init__(self, subjects=("001",), runs=(1,), root=None):
        self.root = Path(root).expanduser() if root else _data_dir() / "hf" / "duin"
        self.runs = list(runs)
        super().__init__(subjects=list(subjects), sessions_per_subject=1, events=None, code="DuIN-2024",
                         paradigm="speech", interval=[0.0, 1.0], sfreq=float("nan"))

    def data_path(self, subject):
        paths = []
        for r in self.runs:
            base = f"data/seeg.he2023xuanwu/{subject}/word-recitation/run{r}/dataset.bipolar.default.unaligned/"
            for name in ("data", "info"):
                paths.append(_download(_HF.format(repo=self.REPO, path=base + name),
                                       self.root / f"{subject}_run{r}_{name}"))
        return paths

    @staticmethod
    def _load_pickle(path):
        """Unpickle a Du-IN file, mapping the project's ``utils.DotDict.DotDict`` class onto :class:`_DotDict`.

        The files were pickled with ``from utils.DotDict import DotDict`` (module path ``utils.DotDict``); older
        exports reference plain ``utils``. Overriding ``find_class`` covers both without touching ``sys.modules``.
        """

        class _Unpickler(pickle.Unpickler):
            def find_class(self, module, name):
                if name == "DotDict" and module.split(".")[0] == "utils":
                    return _DotDict
                return super().find_class(module, name)

        with open(path, "rb") as fh:
            return _Unpickler(fh).load()

    def _get_single_subject_data(self, subject):
        out = {}
        paths = self.data_path(subject)
        for r in self.runs:
            data_p = next(p for p in paths if p.name == f"{subject}_run{r}_data")
            info_p = next(p for p in paths if p.name == f"{subject}_run{r}_info")
            info = self._load_pickle(info_p)
            trials = self._load_pickle(data_p)
            ch_names = list(info.get("ch_names", []))
            sfreq = float(info.get("sfreq", info.get("sample_rate", 1000.0)) or 1000.0)
            X, names = [], []
            for tr in trials:
                arr = np.asarray(tr.get("data_s", tr.get("data")), dtype=float)
                X.append(arr)
                names.append(str(tr.get("name", "?")))
            n_t = min(a.shape[-1] for a in X)
            X = np.stack([a[..., :n_t] if a.shape[0] == len(ch_names) or a.ndim == 2 else a.T[..., :n_t] for a in X])
            if X.shape[1] != len(ch_names):
                X = np.transpose(X, (0, 2, 1))[:, :, :n_t]
            labels = sorted(set(names))
            event_id = {lab: i + 1 for i, lab in enumerate(labels)}
            events = np.column_stack([np.arange(len(X)) * n_t, np.zeros(len(X), int),
                                      [event_id[n] for n in names]])
            info_m = mne.create_info(ch_names or [f"E{i + 1:03d}" for i in range(X.shape[1])], sfreq,
                                     ["ecog"] * X.shape[1])
            epochs = mne.EpochsArray(X * 1e-6, info_m, events=events, event_id=event_id, tmin=0.0,
                                     verbose=False)
            out.setdefault("0", {})[f"run{r}"] = epochs
            self.event_id = event_id
        return out


class SWEC(_SimpleDataset):
    """SWEC long-term iEEG (HF NeuroTec/SWEC_iEEG_Dataset, CDLA-Permissive-2.0), one part file."""

    REPO = "NeuroTec/SWEC_iEEG_Dataset"

    def __init__(self, subjects=("ID01",), parts=(1,), root=None, max_seconds=600.0):
        self.root = Path(root).expanduser() if root else _data_dir() / "hf" / "swec"
        self.parts = list(parts)
        self.max_seconds = max_seconds
        super().__init__(subjects=list(subjects), sessions_per_subject=1, events=None, code="SWEC-iEEG",
                         paradigm="clinical", interval=None, sfreq=float("nan"))

    def data_path(self, subject):
        return [_download(_HF.format(repo=self.REPO, path=f"{subject}/{subject}_part_{p}.h5"),
                          self.root / f"{subject}_part_{p}.h5") for p in self.parts]

    def _get_single_subject_data(self, subject):
        import h5py

        _load_hdf5_plugins()
        out = {}
        for path in self.data_path(subject):
            with h5py.File(path, "r") as f:
                dsets = {}
                f.visititems(lambda n, o: dsets.__setitem__(n, o) if isinstance(o, h5py.Dataset) else None)
                big = max(dsets, key=lambda k: np.prod(dsets[k].shape))
                d = dsets[big]
                sfreq = float(f.attrs.get("fs", f.attrs.get("sampling_rate", 512.0)))
                for k in ("fs", "sfreq", "sampling_rate"):
                    if k in dsets and np.prod(dsets[k].shape) == 1:
                        sfreq = float(np.asarray(dsets[k][()]).ravel()[0])
                n = int(min(d.shape[0] if d.shape[0] > d.shape[-1] else d.shape[-1], self.max_seconds * sfreq))
                arr = np.asarray(d[:n, :] if d.shape[0] > d.shape[-1] else d[:, :n], dtype=float)
                if arr.shape[0] > arr.shape[1]:
                    arr = arr.T
            raw = _raw_from_array(arr * 1e-6, sfreq, description=f"SWEC {path.stem} ({big})")
            out.setdefault("0", {})[path.stem] = raw
        return out


class OmniEDF(_SimpleDataset):
    """Omni-iEEG raw 10-min EDF clips (HF Dadaism6/Omni-iEEG-Raw-Event-EDF)."""

    REPO = "Dadaism6/Omni-iEEG-Raw-Event-EDF"

    def __init__(self, files=("Pt1_AR_original_mne_griddep_10min.edf",), root=None):
        self.root = Path(root).expanduser() if root else _data_dir() / "hf" / "omni_edf"
        self.files = list(files)
        super().__init__(subjects=[f.split("_")[0] for f in self.files], sessions_per_subject=1,
                         events=None, code="OmniiEEG-EDF", paradigm="clinical", interval=None,
                         sfreq=float("nan"))

    def data_path(self, subject):
        return [_download(_HF.format(repo=self.REPO, path=f), self.root / f) for f in self.files
                if f.startswith(subject + "_")]

    def _get_single_subject_data(self, subject):
        out = {}
        for path in self.data_path(subject):
            raw = mne.io.read_raw_edf(path, preload=True, verbose=False)
            raw.set_channel_types({ch: "ecog" for ch in raw.ch_names}, verbose=False)
            out.setdefault("0", {})[path.stem] = raw
        return out


class MindEyeIEEG(_SimpleDataset):
    """iEEG Natural Scenes derivatives (HF rishab-iyer1/mindeye_ieeg): high-frequency broadband per image."""

    REPO = "rishab-iyer1/mindeye_ieeg"

    def __init__(self, root=None, load_array=False):
        self.root = Path(root).expanduser() if root else _data_dir() / "hf" / "mindeye"
        self.load_array = load_array
        super().__init__(subjects=["all"], sessions_per_subject=1, events=None, code="MindEye-iEEG-NSD",
                         paradigm="visual", interval=None, sfreq=float("nan"))

    def data_path(self, subject):
        files = ["derivatives/hfb/channel_info.csv", "derivatives/hfb/stim_info.pkl"]
        if self.load_array:
            files.append("derivatives/hfb/reshaped_electrode_data.npy")
        return [_download(_HF.format(repo=self.REPO, path=f), self.root / Path(f).name) for f in files]

    def _get_single_subject_data(self, subject):
        import pandas as pd

        paths = self.data_path(subject)
        chans = pd.read_csv(paths[0])
        arr_path = self.root / "reshaped_electrode_data.npy"
        if arr_path.is_file():
            arr = np.load(arr_path, mmap_mode="r")
            shape = arr.shape
        else:
            shape = None
        raw = _raw_from_array(np.zeros((len(chans), 10)), 1.0,
                              [str(c) for c in chans.iloc[:, 0]], ["ecog"] * len(chans),
                              description=f"mindeye derivative array shape {shape}")
        return {"0": {"0": raw}}


# ------------------------------------------------------------------ Brain Treebank
class BrainTreebank(_SimpleDataset):
    """Brain Treebank (braintreebank.dev, CC-BY-4.0): one trial HDF5 per movie viewing."""

    BASE = "https://braintreebank.dev/data/"

    def __init__(self, subjects=("1",), trials=(0,), root=None, max_seconds=600.0):
        self.root = Path(root).expanduser() if root else _data_dir() / "braintreebank"
        self.trials = list(trials)
        self.max_seconds = max_seconds
        super().__init__(subjects=list(subjects), sessions_per_subject=1, events=None,
                         code="BrainTreebank", paradigm="naturalistic", interval=None, sfreq=2048.0)

    def data_path(self, subject):
        paths = []
        for t in self.trials:
            name = f"sub_{subject}_trial{t:03d}.h5"
            z = _download(self.BASE + f"subject_data/sub_{subject}/trial{t:03d}/{name}.zip",
                          self.root / f"{name}.zip")
            h5 = self.root / name
            if not h5.is_file():
                with zipfile.ZipFile(z) as zf:
                    zf.extractall(self.root)
                found = next(self.root.rglob(name), None)
                if found and found != h5:
                    shutil.move(str(found), str(h5))
            paths.append(h5)
        return paths

    def _get_single_subject_data(self, subject):
        import h5py

        out = {}
        for path in self.data_path(subject):
            with h5py.File(path, "r") as f:
                grp = f["data"] if "data" in f else f
                keys = sorted(k for k in grp.keys() if isinstance(grp[k], h5py.Dataset))
                n = int(min(grp[keys[0]].shape[0], self.max_seconds * 2048))
                arr = np.stack([np.asarray(grp[k][:n], dtype=float) for k in keys])
            raw = _raw_from_array(arr * 1e-6, 2048.0, keys, ["ecog"] * len(keys),
                                  description=f"BrainTreebank {path.stem}")
            out.setdefault("0", {})[path.stem] = raw
        return out


__all__ = ["BCICompIV4", "BCICompIII1", "PetersonMoveRest", "PetersonPose", "PetersonReach",
           "RogersMicroECoG", "VerwoertSpeech", "MerkGripForce", "DuIN", "SWEC", "OmniEDF",
           "MindEyeIEEG", "BrainTreebank"]


# ------------------------------------------------------------------ Zenodo (Bellier music)
class BellierMusic(_SimpleDataset):
    """Bellier 2023 music reconstruction: high-frequency activity (70-150 Hz) of 29 patients (Zenodo 7876019, CC-BY).

    Each ``P{n}_HFA_data.mat`` holds ``ecog`` (time x electrodes) at 100 Hz while the patient listened to
    190.7 s of Pink Floyd's "Another Brick in the Wall, Part 1"; ``thewall1_stim32.mat`` is the 32-band
    auditory spectrogram of the song on the same time base. The loader returns one Raw per patient: HFA
    channels typed ``ecog`` (feature domain, already rectified and z-scored by the authors) plus 32 ``misc``
    channels ``stim_<Hz>`` carrying the spectrogram, so the regression target lives next to the features.
    Electrodes flagged noisy or epileptic by the authors go to ``info["bads"]``; MNI coordinates come from
    ``P{n}_MNI_electrode_coordinates.mat``.
    """

    RECORD = 7876019
    URL = "https://zenodo.org/api/records/{rec}/files/{name}/content"
    ALL = tuple(f"P{i}" for i in range(1, 30))

    def __init__(self, subjects=ALL, root=None):
        self.root = Path(root).expanduser() if root else _data_dir() / "zenodo" / "bellier"
        super().__init__(subjects=list(subjects), sessions_per_subject=1, events=None, code="Bellier2023-music",
                         paradigm="stimulus-reconstruction", interval=None, sfreq=100.0,
                         doi="10.1371/journal.pbio.3002176")

    def _file(self, name):
        return _download(self.URL.format(rec=self.RECORD, name=name), self.root / name)

    def data_path(self, subject):
        return [self._file(f"{subject}_HFA_data.mat"), self._file("thewall1_stim32.mat"),
                self._file(f"{subject}_MNI_electrode_coordinates.mat")]

    def _get_single_subject_data(self, subject):
        import scipy.io as sio

        hfa_p, stim_p, _ = self.data_path(subject)
        m = sio.loadmat(hfa_p, squeeze_me=True, struct_as_record=False)
        x = np.asarray(m["ecog"], dtype=float).T  # (n_elec, n_times)
        info = m["dataInfo"]
        fs = float(getattr(info, "fs", 100.0))
        stim = np.asarray(sio.loadmat(stim_p, squeeze_me=True)["stim32"], dtype=float).T
        cf = np.asarray(sio.loadmat(stim_p, squeeze_me=True)["CF32"]).ravel()
        n = min(x.shape[1], stim.shape[1])
        names = [f"E{i + 1:03d}" for i in range(x.shape[0])] + [f"stim_{int(round(float(c)))}Hz" for c in cf]
        types = ["ecog"] * x.shape[0] + ["misc"] * stim.shape[0]
        raw = _raw_from_array(np.vstack([x[:, :n], stim[:, :n]]), fs, ch_names=names, ch_types=types,
                              description=f"Bellier HFA (z-scored 70-150 Hz envelope) {subject}; "
                                          "32-band song spectrogram as misc")
        bads = set()
        for attr in ("idxNoisyElecs", "idxEpilepticElecs"):
            idx = np.atleast_1d(np.asarray(getattr(info, attr, []), dtype=float)).astype(int)
            bads.update(f"E{i:03d}" for i in idx if 1 <= i <= x.shape[0])  # MATLAB 1-based indices
        raw.info["bads"] = sorted(bads)
        return {"0": {"0": raw}}

    def get_electrode_info(self, subject):
        import scipy.io as sio

        from .base import ElectrodeInfo

        m = sio.loadmat(self.data_path(subject)[2], squeeze_me=True, struct_as_record=False)
        e = m[next(k for k in m if not k.startswith("__"))]
        pos = np.asarray(e.elecpos, dtype=float)
        labels = [f"E{i + 1:03d}" for i in range(pos.shape[0])]
        anat = [str(a) for a in np.atleast_1d(getattr(e, "anatLabels", []))] or None
        return ElectrodeInfo(positions=pos, labels=labels, coord_frame="mni", gyrus=anat)


# ------------------------------------------------------------------ OSF (Stolk sensorimotor)
class StolkSensorimotor(_SimpleDataset):
    """Stolk 2019 eLife sensorimotor alpha/beta: high-density ECoG, FieldTrip trials (OSF z4hfm).

    ``S{n}_raw_segmented.mat`` (MATLAB v5) holds a FieldTrip raw structure: ``trial`` (cells of channels x
    2049 samples, -1.5 to 2.5 s around the cue at 512 Hz), ``label``, ``trialinfo`` (49 x 9) and ``elec``
    (positions in mm). The columns of ``trialinfo`` are not documented in the deposit; columns 1-4 are
    binary condition codes and column 5 a reaction time. ``label_column`` picks the one used as the class
    (default 2, two balanced values), so treat the resulting labels as *condition code*, not a named
    movement, until the authors' analysis code is cross-checked (paper: Stolk et al. 2019, eLife 8:e48065).
    """

    FILES = {"S4": "mgn6y", "S5": "qmsc4", "S6": "dtqky"}

    def __init__(self, subjects=("S4", "S5", "S6"), root=None, label_column=2):
        self.root = Path(root).expanduser() if root else _data_dir() / "osf" / "stolk"
        self.label_column = int(label_column)
        super().__init__(subjects=list(subjects), sessions_per_subject=1, events=None, code="Stolk2019-sensorimotor",
                         paradigm="motor", interval=[0.0, 1.0], sfreq=512.0, doi="10.7554/eLife.48065")

    def data_path(self, subject):
        return [_download(f"https://osf.io/download/{self.FILES[subject]}/",
                          self.root / f"{subject}_raw_segmented.mat")]

    def _get_single_subject_data(self, subject):
        import scipy.io as sio

        d = sio.loadmat(self.data_path(subject)[0], squeeze_me=True, struct_as_record=False)["data"]
        trials = [np.asarray(t, dtype=float) for t in d.trial]
        n_t = min(t.shape[1] for t in trials)
        X = np.stack([t[:, :n_t] for t in trials]) * 1e-6  # FieldTrip data in microvolts
        labels = [str(lab) for lab in np.atleast_1d(d.label)]
        fs = float(d.fsample)
        tmin = float(np.asarray(d.time[0]).ravel()[0])
        info_ = np.asarray(d.trialinfo, dtype=float)
        codes = info_[:, self.label_column]
        classes = sorted(set(codes.tolist()))
        self.event_id = {f"cond{int(c) if float(c).is_integer() else c}": i + 1 for i, c in enumerate(classes)}
        events = np.column_stack([np.arange(len(codes)) * (n_t + 1), np.zeros(len(codes), int),
                                  [self.event_id[f"cond{int(c) if float(c).is_integer() else c}"] for c in codes]])
        info = mne.create_info(labels, fs, ["ecog"] * len(labels))
        epochs = mne.EpochsArray(X, info, events=events, event_id=self.event_id, tmin=tmin, verbose=False)
        epochs.info["description"] = f"Stolk 2019 {subject}; classes = trialinfo column {self.label_column}"
        return {"0": {"0": epochs}}

    def get_electrode_info(self, subject):
        import scipy.io as sio

        from .base import ElectrodeInfo

        d = sio.loadmat(self.data_path(subject)[0], squeeze_me=True, struct_as_record=False)["data"]
        e = d.elec
        return ElectrodeInfo(positions=np.asarray(e.elecpos, dtype=float),
                             labels=[str(lab) for lab in np.atleast_1d(e.label)], coord_frame="unknown")


# ------------------------------------------------------------------ DANDI 001535 (BRAVO neural features)
class BRAVOFeatures(_SimpleDataset):
    """DANDI 001535: long-term BCI training data of a tetraplegic participant (BRAVO1), neural features per trial.

    The NWB holds no voltage: each ``acquisition/trial_<k>`` is a (time x 256) TimeSeries of neural features
    (the Chang-lab high-gamma and low-frequency streams over the 128-channel array) with timestamps, and
    ``intervals/trials`` gives ``target_id`` (the cued target), ``is_robot`` and ``is_virtual``. The loader
    turns the first ``max_trials`` trials into an ``EpochsArray`` cropped to the shortest trial, labelled by
    ``target_id``, so target decoding runs like any other epoched paradigm; the channels are typed ``ecog``
    but are *features*, which the description records.
    """

    def __init__(self, subjects=("BRAVO1",), root=None, max_trials=2000, label="target_id", version="draft"):
        self.root = Path(root).expanduser() if root else _data_dir() / "dandi" / "001535"
        self.max_trials = max_trials
        self.label = label
        self.version = version
        super().__init__(subjects=list(subjects), sessions_per_subject=1, events=None, code="DANDI-001535-BRAVO",
                         paradigm="bci-target", interval=[0.0, 0.9], sfreq=float("nan"))

    def data_path(self, subject):
        from .nwb import download_dandi_asset, list_dandi_assets

        dest = self.root / f"sub-{subject}" / f"sub-{subject}.nwb"
        if not dest.is_file():
            assets = [a for a in list_dandi_assets("001535", self.version) if f"sub-{subject}" in a["path"]]
            if not assets:
                raise FileNotFoundError(f"no asset for sub-{subject} in DANDI 001535")
            download_dandi_asset("001535", assets[0], self.root, self.version)
        return [dest]

    def _get_single_subject_data(self, subject):
        import h5py

        path = self.data_path(subject)[0]
        with h5py.File(path, "r") as f:
            tab = f["intervals/trials"]
            ids = np.asarray(tab["id"][()])
            labels = np.asarray(tab[self.label][()])
            order = np.argsort(ids)
            ids, labels = ids[order], labels[order]
            if self.max_trials is not None:
                ids, labels = ids[: self.max_trials], labels[: self.max_trials]
            X, y, rates = [], [], []
            for tid, lab in zip(ids, labels):
                g = f["acquisition"].get(f"trial_{int(tid)}")
                if g is None or not np.isfinite(float(lab)):
                    continue
                data = np.asarray(g["data"][()], dtype=float)  # (time, features)
                ts = np.asarray(g["timestamps"][()], dtype=float) if "timestamps" in g else None
                if ts is not None and ts.size > 1:
                    rates.append(1.0 / float(np.median(np.diff(ts))))
                X.append(data.T)
                y.append(lab)
        if not X:
            raise ValueError(f"{path}: no usable trials")
        sfreq = float(np.median(rates)) if rates else 200.0
        n_t = min(x.shape[1] for x in X)
        X = np.stack([x[:, :n_t] for x in X])
        classes = sorted(set(float(v) for v in y))
        self.event_id = {f"target{int(c)}": i + 1 for i, c in enumerate(classes)}
        events = np.column_stack([np.arange(len(y)) * (n_t + 1), np.zeros(len(y), int),
                                  [self.event_id[f"target{int(c)}"] for c in y]])
        names = [f"f{i + 1:03d}" for i in range(X.shape[1])]
        info = mne.create_info(names, sfreq, ["ecog"] * len(names))
        epochs = mne.EpochsArray(X, info, events=events, event_id=self.event_id, tmin=0.0, verbose=False)
        epochs.info["description"] = ("BRAVO1 neural features (256 = high-gamma + low-frequency streams of 128 "
                                      f"channels) at {sfreq:.0f} Hz; first {len(y)} trials cropped to {n_t} samples; "
                                      f"label {self.label}")
        return {"0": {"0": epochs}}
