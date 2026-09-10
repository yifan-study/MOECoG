"""Generic loader for BIDS-iEEG datasets (OpenNeuro and local).

One class covers most of the public intracranial corpora in
``docs/dataset_catalog.md``: the Podcast dataset, the Utrecht film dataset,
the Visual ECoG dataset, the Detroit naming corpus, the RAM memory datasets,
the CCEP sets, and Cogitate once registered. Events come from
``*_events.tsv`` (column ``trial_type`` by default), electrode coordinates
from ``*_electrodes.tsv`` and ``*_coordsystem.json``.

Downloads use ``openneuro-py`` (``pip install openneuro-py``); reading uses
``mne-bids``. Set ``MOECOG_DATA_DIR`` (default ``~/moecog_data``) to control
where datasets are cached (``<data_dir>/openneuro/<dataset_id>``).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import mne
import numpy as np

from .base import BaseECoGDataset, ElectrodeInfo

_IEEG_TYPES = ("ecog", "seeg", "dbs")


def _data_dir() -> Path:
    return Path(os.environ.get("MOECOG_DATA_DIR", "~/moecog_data")).expanduser()


class BIDSiEEGDataset(BaseECoGDataset):
    """A BIDS-iEEG dataset exposed through the MOECoG interface.

    Parameters
    ----------
    root : str or Path or None
        BIDS root. None with ``openneuro_id`` uses the cache directory.
    openneuro_id : str or None
        OpenNeuro accession (``"ds005953"``); the dataset is downloaded on first
        use when ``download=True``.
    task : str or None
        BIDS task label to load (None loads every task, each as a run).
    events : dict or None
        ``{name: id}`` restricting the annotations kept from ``trial_type``.
        None keeps every distinct trial_type and numbers them.
    event_column : str
        events.tsv column holding the class label.
    interval : list of float or None
        Default epoch window relative to onset (needed for classification).
    paradigm : str
        Paradigm family tag.
    channel_types : tuple of str
        Which iEEG channel types count as data (``ecog`` only, or with
        ``seeg``). Others are dropped.
    subjects : list of str or None
        Subset of BIDS subject labels (without ``sub-``).
    code : str or None
        Dataset code; defaults to the accession or root name.
    download : bool
    include : list of str or None
        openneuro-py include patterns (for example ``["sub-01/*"]``) to fetch
        a subset.
    """

    def __init__(self, root=None, openneuro_id=None, task=None, events=None,
                 event_column="trial_type", interval=None, paradigm="epoched",
                 channel_types=("ecog",), subjects=None, code=None, download=True,
                 include=None, sfreq=None):
        if root is None and openneuro_id is None:
            raise ValueError("Give root or openneuro_id")
        self.openneuro_id = openneuro_id
        self._root = Path(root).expanduser() if root else _data_dir() / "openneuro" / openneuro_id
        self.task = task
        self.event_column = event_column
        self.channel_types = tuple(channel_types)
        self.download = download
        self.include = include
        self._requested_subjects = subjects
        self._events = dict(events) if events else None
        self._ensure_downloaded()
        subs = self._list_subjects()
        if subjects is not None:
            missing = [s for s in subjects if s not in subs]
            if missing:
                raise ValueError(f"Subjects {missing} not in {self._root}")
            subs = list(subjects)
        super().__init__(
            subjects=subs,
            sessions_per_subject=max(1, max((len(self._sessions(s)) for s in subs), default=1)),
            events=self._events,
            code=code or (openneuro_id or self._root.name),
            paradigm=paradigm,
            interval=interval,
            sfreq=sfreq if sfreq is not None else float("nan"),
        )

    # -- discovery -------------------------------------------------------------
    @property
    def root(self) -> Path:
        return self._root

    def _ensure_downloaded(self):
        if (self._root / "dataset_description.json").is_file():
            return
        if not self.download or not self.openneuro_id:
            raise FileNotFoundError(f"No BIDS dataset at {self._root}")
        import openneuro

        self._root.mkdir(parents=True, exist_ok=True)
        openneuro.download(dataset=self.openneuro_id, target_dir=self._root,
                           include=self.include)

    def _list_subjects(self):
        subs = sorted(p.name[4:] for p in self._root.glob("sub-*") if p.is_dir())
        return [s for s in subs if self._ieeg_files(s)]

    def _ieeg_files(self, subject):
        pattern = f"sub-{subject}_*_ieeg.*"
        files = [f for f in self._root.glob(f"sub-{subject}/**/ieeg/{pattern}")
                 if f.suffix in (".vhdr", ".edf", ".set", ".fif", ".nwb", ".mefd", ".bdf")
                 or f.suffix == ".eeg" and False]
        files = [f for f in files if not f.name.endswith(("_events.tsv", "_channels.tsv",
                                                          "_electrodes.tsv", ".json"))]
        if self.task:
            files = [f for f in files if f"_task-{self.task}_" in f.name]
        return sorted(files)

    def _sessions(self, subject):
        sess = set()
        for f in self._ieeg_files(subject):
            m = re.search(r"_ses-([A-Za-z0-9]+)_", f.name)
            sess.add(m.group(1) if m else "0")
        return sorted(sess)

    def data_path(self, subject):
        self._ensure_downloaded()
        return self._ieeg_files(subject)

    # -- loading -------------------------------------------------------------------
    def _load_file(self, path: Path):
        from mne_bids import BIDSPath, read_raw_bids

        ent = dict(subject=None, session=None, task=None, run=None, acquisition=None)
        for key, pat in (("subject", r"sub-([A-Za-z0-9]+)"), ("session", r"ses-([A-Za-z0-9]+)"),
                         ("task", r"task-([A-Za-z0-9]+)"), ("run", r"run-([A-Za-z0-9]+)"),
                         ("acquisition", r"acq-([A-Za-z0-9]+)")):
            m = re.search(pat, path.name)
            if m:
                ent[key] = m.group(1)
        bp = BIDSPath(root=self._root, datatype="ieeg", suffix="ieeg",
                      extension=path.suffix, **{k: v for k, v in ent.items() if v})
        with mne.utils.use_log_level("error"):
            raw = read_raw_bids(bp, verbose=False)
        raw.load_data()
        keep = [ch for ch, t in zip(raw.ch_names, raw.get_channel_types())
                if t in self.channel_types or t in ("stim", "misc")]
        raw.pick(keep)
        # rename non-ecog data channels to 'ecog' so paradigms see one data type
        types = {ch: "ecog" for ch, t in zip(raw.ch_names, raw.get_channel_types())
                 if t in _IEEG_TYPES}
        if types:
            raw.set_channel_types(types, verbose=False)
        if self._events is not None:
            keep_desc = set(self._events)
            ann = raw.annotations
            mask = np.array([d in keep_desc for d in ann.description], dtype=bool)
            raw.set_annotations(ann[mask] if len(ann) else ann)
        return raw, ent

    def _get_single_subject_data(self, subject):
        out = {}
        for f in self._ieeg_files(subject):
            raw, ent = self._load_file(f)
            session = ent["session"] or "0"
            run = "_".join(x for x in (ent["task"], ent["run"], ent["acquisition"]) if x) or "0"
            out.setdefault(session, {})[run] = raw
            if self._events is None:
                # discover labels from annotations
                labels = sorted(set(raw.annotations.description))
                current = self.event_id or {}
                for lab in labels:
                    if lab not in current:
                        current[lab] = len(current) + 1
                self.event_id = current
        return out

    def get_electrode_info(self, subject):
        import pandas as pd

        files = sorted(self._root.glob(f"sub-{subject}/**/ieeg/*_electrodes.tsv"))
        if not files:
            raise FileNotFoundError(f"No electrodes.tsv for sub-{subject}")
        df = pd.read_csv(files[0], sep="\t")
        pos = df[["x", "y", "z"]].to_numpy(dtype=float)
        frame = "unknown"
        coord = list(files[0].parent.glob("*_coordsystem.json"))
        if coord:
            import json

            frame = json.load(open(coord[0])).get("iEEGCoordinateSystem", "unknown").lower()
        return ElectrodeInfo(positions=pos, labels=df["name"].astype(str).tolist(),
                             coord_frame=frame)

    def __repr__(self):
        return (f"BIDSiEEGDataset(code={self.code!r}, root={str(self._root)!r}, "
                f"subjects={len(self.subject_list)})")


# Named datasets from the catalog -------------------------------------------------

def HermesVisualECoG(**kw):
    """OpenNeuro ds005953: 2 ECoG subjects, visual gratings/noise (Hermes 2015, 2017)."""
    return BIDSiEEGDataset(openneuro_id="ds005953", task="visual", interval=[0.0, 0.5],
                           paradigm="visual", code="Hermes2015-visual", **kw)


def PodcastECoG(**kw):
    """OpenNeuro ds005574: 9 patients listening to a 30-min podcast (Zada 2025)."""
    return BIDSiEEGDataset(openneuro_id="ds005574", task="podcast", paradigm="naturalistic",
                           channel_types=("ecog", "seeg"), code="Podcast2025", **kw)


def FilmIEEG(**kw):
    """OpenNeuro ds003688: 51 iEEG patients watching a short film (Berezutskaya 2022)."""
    return BIDSiEEGDataset(openneuro_id="ds003688", task="film", paradigm="naturalistic",
                           channel_types=("ecog", "seeg"), code="Film2022", **kw)


def VisualECoG(**kw):
    """OpenNeuro ds004194: 14 patients, visual pRF/pattern tasks (Groen 2022)."""
    return BIDSiEEGDataset(openneuro_id="ds004194", paradigm="visual", interval=[0.0, 0.5],
                           channel_types=("ecog",), code="VisualECoG2022", **kw)


__all__ = ["BIDSiEEGDataset", "HermesVisualECoG", "PodcastECoG", "FilmIEEG", "VisualECoG"]
