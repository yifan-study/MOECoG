"""Generic loader for NWB files and DANDI dandisets.

Covers the DANDI entries of the catalog (AJILE12, Bouchard/Chang syllables,
Natraj long-term BCI, Rutishauser cognitive sets) and NWB files inside
BIDS-like layouts (Verwoert speech production). An ``ElectricalSeries`` (or
the first one holding iEEG) becomes the ECoG channels of an :class:`mne.io.Raw`;
trial tables (``nwb.trials``, ``nwb.intervals``) become annotations.

Downloads go through the DANDI REST API (no login) into
``$MOECOG_DATA_DIR/dandi/<dandiset>/<asset path>``; assets are chosen by path
pattern and can be capped by size so smoke tests stay cheap.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

import mne
import numpy as np

from .base import BaseECoGDataset, ElectrodeInfo

DANDI_API = "https://api.dandiarchive.org/api"


def _data_dir() -> Path:
    return Path(os.environ.get("MOECOG_DATA_DIR", "~/moecog_data")).expanduser()


def _get_json(url):
    headers = {"User-Agent": "moecog/0.2", "Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers)
    return json.load(urllib.request.urlopen(req, timeout=120))


def list_dandi_assets(dandiset: str, version: str = "draft"):
    """Return ``[{"path", "size", "asset_id"}, ...]`` for a dandiset."""
    url = f"{DANDI_API}/dandisets/{dandiset}/versions/{version}/assets/?page_size=1000"
    out = []
    while url:
        r = _get_json(url)
        out += [{"path": a["path"], "size": a["size"], "asset_id": a["asset_id"]}
                for a in r["results"]]
        url = r.get("next")
    return out


def download_dandi_asset(dandiset: str, asset: dict, target_root: Path, version: str = "draft"):
    """Download one asset (streamed) if it is not already present with the right size."""
    dest = target_root / asset["path"]
    if dest.is_file() and dest.stat().st_size == asset["size"]:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{DANDI_API}/assets/{asset['asset_id']}/download/"
    req = urllib.request.Request(url, headers={"User-Agent": "moecog/0.2"})
    with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as fh:
        while True:
            chunk = resp.read(1 << 22)
            if not chunk:
                break
            fh.write(chunk)
    return dest


def read_nwb_raw(path, series=None, channel_types=("ecog", "seeg", "ieeg"), trials_table=None,
                 label_column=None, max_seconds=None):
    """Read an NWB file into ``(raw, meta)``.

    Parameters
    ----------
    path : str or Path
    series : str or None
        Name of the ``ElectricalSeries`` to use; None picks the first one
        whose electrodes are iEEG (or the largest one).
    trials_table : str or None
        ``"trials"`` or a key of ``nwb.intervals``; None tries ``trials`` then
        every interval table.
    label_column : str or None
        Column of the trials table used as the annotation description; None
        uses the first non-time column.
    max_seconds : float or None
        Read only the first ``max_seconds`` of the series (smoke tests).
    """
    from pynwb import NWBHDF5IO

    meta = {"path": str(path)}
    with NWBHDF5IO(str(path), "r", load_namespaces=True) as io:
        nwb = io.read()
        candidates = {}
        def collect(container):
            for name, obj in getattr(container, "items", lambda: [])():
                if obj.__class__.__name__ == "ElectricalSeries":
                    candidates[name] = obj
        collect(nwb.acquisition)
        for mod in nwb.processing.values():
            for name, obj in mod.data_interfaces.items():
                if obj.__class__.__name__ == "ElectricalSeries":
                    candidates[f"{mod.name}/{name}"] = obj
                elif obj.__class__.__name__ == "LFP":
                    for n2, es in obj.electrical_series.items():
                        candidates[f"{mod.name}/{name}/{n2}"] = es
        series_type = "ElectricalSeries"
        if not candidates:
            # some deposits (Verwoert 2022 single-word production) store the voltage as a plain 2-D
            # TimeSeries named e.g. "iEEG" with no electrodes table; accept those before giving up
            plain = {}
            for name, obj in getattr(nwb.acquisition, "items", lambda: [])():
                if obj.__class__.__name__ == "TimeSeries" and getattr(obj.data, "ndim", 0) == 2:
                    plain[name] = obj
            named = {k: v for k, v in plain.items()
                     if re.search(r"ieeg|ecog|seeg|lfp|eeg|neural|voltage|raw", k, re.IGNORECASE)}
            candidates = named or (plain if series in plain else {})
            series_type = "TimeSeries"
        if not candidates:
            raise ValueError(f"No ElectricalSeries in {path}")
        if series is None:
            series = max(candidates, key=lambda k: int(np.prod(candidates[k].data.shape)))
        es = candidates[series]
        meta["series"] = series
        meta["series_type"] = series_type
        meta["all_series"] = list(candidates)
        rate = es.rate
        if rate is None:
            ts = es.timestamps[:2]
            rate = 1.0 / float(ts[1] - ts[0])
        n_times = es.data.shape[0]
        if max_seconds is not None:
            n_times = min(n_times, int(max_seconds * rate))
        data = np.asarray(es.data[:n_times, :], dtype=float).T  # (n_ch, n_times)
        conv = getattr(es, "conversion", 1.0) or 1.0
        data *= conv
        # electrodes (a plain TimeSeries has none)
        elec = getattr(es, "electrodes", None)
        try:
            edf = elec.to_dataframe() if elec is not None else None
        except Exception:
            edf = None
        names, types, pos = [], [], None
        if edf is not None:
            for i, (_, row) in enumerate(edf.iterrows()):
                nm = str(row.get("label", row.get("location", f"E{i + 1:03d}")))
                names.append(nm if nm and nm != "nan" else f"E{i + 1:03d}")
                grp = str(row.get("group_name", "")).lower()
                t = "ecog" if ("grid" in grp or "strip" in grp or "ecog" in grp) else (
                    "seeg" if ("depth" in grp or "seeg" in grp or "probe" in grp) else "ecog")
                types.append(t)
            if all(c in edf.columns for c in ("x", "y", "z")):
                pos = edf[["x", "y", "z"]].to_numpy(dtype=float)
        else:
            names = [f"E{i + 1:03d}" for i in range(data.shape[0])]
            types = ["ecog"] * data.shape[0]
        # unique names
        seen = {}
        for i, nm in enumerate(names):
            if nm in seen:
                seen[nm] += 1
                names[i] = f"{nm}_{seen[nm]}"
            else:
                seen[nm] = 0
        ch_types = ["ecog" if t in channel_types else "misc" for t in types]
        info = mne.create_info(names, rate, ch_types)
        raw = mne.io.RawArray(data, info, verbose=False)
        # annotations from trial/interval tables
        onsets, durs, descs = [], [], []
        tables = {}
        if nwb.trials is not None:
            tables["trials"] = nwb.trials
        for k, v in nwb.intervals.items():
            tables.setdefault(k, v)
        chosen = [trials_table] if trials_table else list(tables)
        for key in chosen:
            tab = tables.get(key)
            if tab is None:
                continue
            df = tab.to_dataframe()
            skip = ("start_time", "stop_time", "timeseries", "tags")
            cols = [c for c in df.columns if c not in skip]
            lab = label_column if label_column in df.columns else (cols[0] if cols else None)
            t0 = raw.times[0]
            for _, row in df.iterrows():
                st, sp = float(row["start_time"]), float(row["stop_time"])
                if max_seconds is not None and st > max_seconds:
                    continue
                onsets.append(st - t0)
                durs.append(max(sp - st, 0.0))
                descs.append(f"{key}/{row[lab]}" if lab else key)
        if onsets:
            raw.set_annotations(mne.Annotations(onsets, durs, descs))
        meta.update({"n_times_total": int(es.data.shape[0]), "sfreq": float(rate),
                     "tables": list(tables), "n_annotations": len(onsets)})
        electrode_info = None
        if pos is not None and len(pos) == len(names):
            electrode_info = ElectrodeInfo(positions=pos, labels=names, coord_frame="unknown")
    return raw, meta, electrode_info


class DANDIDataset(BaseECoGDataset):
    """One dandiset exposed through the MOECoG interface.

    Parameters
    ----------
    dandiset : str
        Six-digit accession (``"001535"``).
    subject_pattern : str
        Regex with one group extracting the subject label from an asset path.
    include : str or None
        Regex an asset path must match (choose sessions or files).
    max_asset_gb : float or None
        Skip assets larger than this (smoke tests).
    max_seconds : float or None
        Read only the first seconds of each file.
    events : dict or None
        ``{name: id}`` of annotation descriptions to keep; None keeps all and
        numbers them after loading.
    """

    def __init__(self, dandiset, subject_pattern=r"sub-([A-Za-z0-9]+)", include=None,
                 max_asset_gb=None, max_seconds=None, events=None, series=None,
                 trials_table=None, label_column=None, paradigm="nwb", interval=None,
                 code=None, root=None, download=True, version="draft"):
        self.dandiset = dandiset
        self.version = version
        self.subject_pattern = subject_pattern
        self.include = include
        self.max_asset_gb = max_asset_gb
        self.max_seconds = max_seconds
        self.series = series
        self.trials_table = trials_table
        self.label_column = label_column
        self.download = download
        self._root = Path(root).expanduser() if root else _data_dir() / "dandi" / dandiset
        self.assets = [a for a in list_dandi_assets(dandiset, version)
                       if a["path"].endswith(".nwb")]
        if include:
            self.assets = [a for a in self.assets if re.search(include, a["path"])]
        if max_asset_gb is not None:
            self.assets = [a for a in self.assets if a["size"] <= max_asset_gb * 1e9]
        by_subject = {}
        for a in self.assets:
            m = re.search(subject_pattern, a["path"])
            if m:
                by_subject.setdefault(m.group(1), []).append(a)
        self._by_subject = by_subject
        self._einfo = {}
        super().__init__(subjects=sorted(by_subject), sessions_per_subject=1, events=events,
                         code=code or f"DANDI-{dandiset}", paradigm=paradigm, interval=interval,
                         sfreq=float("nan"))

    @property
    def root(self):
        return self._root

    def data_path(self, subject):
        paths = []
        for a in self._by_subject[subject]:
            if self.download:
                paths.append(download_dandi_asset(self.dandiset, a, self._root, self.version))
            else:
                paths.append(self._root / a["path"])
        return paths

    def _get_single_subject_data(self, subject):
        out = {}
        for i, path in enumerate(self.data_path(subject)):
            raw, meta, einfo = read_nwb_raw(
                path, series=self.series, trials_table=self.trials_table,
                label_column=self.label_column, max_seconds=self.max_seconds,
            )
            m = re.search(r"ses-([A-Za-z0-9]+)", Path(path).name)
            session = m.group(1) if m else str(i)
            out.setdefault(session, {})["0"] = raw
            if einfo is not None:
                self._einfo[subject] = einfo
            if self.event_id is None:
                labels = sorted(set(raw.annotations.description))
                self.event_id = {lab: k + 1 for k, lab in enumerate(labels)} or None
        return out

    def get_electrode_info(self, subject):
        if subject not in self._einfo:
            self._get_single_subject_data(subject)
        if subject not in self._einfo:
            raise FileNotFoundError(f"No electrode coordinates in the NWB files of {subject}")
        return self._einfo[subject]


__all__ = ["DANDIDataset", "read_nwb_raw", "list_dandi_assets", "download_dandi_asset"]
