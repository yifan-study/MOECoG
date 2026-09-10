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
import warnings
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
                 include=None, sfreq=None, max_runs=None, max_seconds=None, mef_password=None):
        if root is None and openneuro_id is None:
            raise ValueError("Give root or openneuro_id")
        #: load at most this many runs per session (sorted file order); None loads everything. Smoke tests
        #: and memory-bound machines use it on datasets with hours-long runs (e.g. the RAM ds0055xx family).
        self.max_runs = max_runs
        #: keep only the first ``max_seconds`` of every run (MEF3 sessions are read partially, other formats
        #: are cropped after loading); None keeps everything.
        self.max_seconds = max_seconds
        #: password for encrypted MEF3 sessions (OpenNeuro deposits are unencrypted: None)
        self.mef_password = mef_password
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
            if missing and subs:
                # the accession's subject list and the folder names can disagree (ds002799):
                # fall back to what was actually downloaded
                import warnings

                warnings.warn(f"{self.code or openneuro_id}: subjects {missing} not found; using {subs[:1]}")
                subs = subs[:1]
            elif missing:
                folders = sorted(p.name for p in self._root.glob("sub-*") if p.is_dir())
                if folders:
                    # e.g. ds002799: sub-* folders carry MRI and iEEG sidecars (channels, electrodes) but no
                    # recordings; the snapshot is metadata-only as far as iEEG goes
                    raise ValueError(f"{self._root}: {len(folders)} sub-* folder(s) but no iEEG recordings, only "
                                     "sidecars/MRI (metadata-only snapshot); nothing else readable")
                raise ValueError(f"Subjects {missing} not in {self._root} and nothing else readable")
            else:
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

    _TOP_FILES = ("dataset_description.json", "participants.tsv", "participants.json", "README",
                  "README.md", "CHANGES")

    def _ensure_downloaded(self):
        if (self._root / "dataset_description.json").is_file() and any(self._root.glob("sub-*")):
            return
        if not self.download or not self.openneuro_id:
            raise FileNotFoundError(f"No BIDS dataset at {self._root}")
        import openneuro

        self._root.mkdir(parents=True, exist_ok=True)
        include = self.include
        if include:
            # directories download recursively; top-level metadata is fetched file by file
            dirs = [i.rstrip("/*") for i in include if i.startswith("sub-")]
            top_patterns = [i for i in include if not i.startswith("sub-")]
            try:
                for attempt in range(2):
                    try:
                        openneuro.download(dataset=self.openneuro_id, target_dir=self._root, include=dirs or None)
                        break
                    except Exception:  # noqa: BLE001
                        if attempt == 1:
                            raise
            except Exception as err:  # noqa: BLE001
                # openneuro-py checks every file with a HEAD request; some datasets (ds006254) answer 403 to
                # HEAD but serve GET, so walk the snapshot through GraphQL and stream the files ourselves
                warnings.warn(f"{self.openneuro_id}: openneuro-py failed ({type(err).__name__}); "
                              "downloading through the GraphQL file tree")
                self._download_via_graphql(dirs, top_patterns)
            for name in self._TOP_FILES:
                if (self._root / name).exists():
                    continue
                try:
                    openneuro.download(dataset=self.openneuro_id, target_dir=self._root, include=[name])
                except Exception:  # noqa: BLE001
                    pass
        else:
            openneuro.download(dataset=self.openneuro_id, target_dir=self._root)
        if not (self._root / "dataset_description.json").is_file():
            (self._root / "dataset_description.json").write_text(
                '{"Name": "%s", "BIDSVersion": "1.7.0"}' % self.openneuro_id)

    _GQL = "https://openneuro.org/crn/graphql"

    def _gql(self, query):
        import json
        import urllib.request

        req = urllib.request.Request(self._GQL, data=json.dumps({"query": query}).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "moecog/0.2"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            out = json.load(resp)
        if out.get("errors"):
            raise RuntimeError(out["errors"][0].get("message", "GraphQL error"))
        return out["data"]

    def _snapshot_files(self, tag, tree_id=None):
        sel = f'(tree:"{tree_id}")' if tree_id else ""
        q = '{ snapshot(datasetId:"%s", tag:"%s"){ files%s { id filename size directory urls } } }' % (
            self.openneuro_id, tag, sel)
        return self._gql(q)["snapshot"]["files"] or []

    def _download_via_graphql(self, dirs, top_patterns):
        """Fetch ``dirs`` (``sub-X`` or ``sub-X/ses-Y`` paths) and matching top-level files with plain GET.

        OpenNeuro's GraphQL tree lists every file with an S3 URL (signed for git-tracked files, versioned
        for annexed ones). GET works on both even when HEAD is refused.
        """
        from fnmatch import fnmatch

        from .misc import _download

        tag = self._gql('{ dataset(id:"%s"){ latestSnapshot { tag } } }' % self.openneuro_id)
        tag = tag["dataset"]["latestSnapshot"]["tag"]
        root = self._snapshot_files(tag)

        def fetch(f, rel):
            dest = self._root / rel
            if dest.is_file() and dest.stat().st_size == int(f["size"]):
                return
            crn = (f"https://openneuro.org/crn/datasets/{self.openneuro_id}/snapshots/{tag}/files/"
                   + rel.replace("/", ":"))
            urls = [u for u in (f.get("urls") or []) if u] + [crn]
            last = None
            for url in urls:  # annexed sidecars can point at another subject's path and answer 403: try the CRN route
                try:
                    _download(url, dest, expected_size=int(f["size"]), retries=2)
                    return
                except OSError as err:
                    last = err
            if rel.endswith(tuple(self._EXT)):
                raise OSError(f"{rel}: {last}")
            warnings.warn(f"{self.openneuro_id}: could not fetch sidecar {rel} ({last})")

        def walk(node, rel):
            for f in self._snapshot_files(tag, node["id"]):
                sub = f"{rel}/{f['filename']}"
                if f["directory"]:
                    walk(f, sub)
                else:
                    fetch(f, sub)

        for f in root:
            if f["directory"]:
                for d in dirs:
                    parts = d.split("/")
                    if f["filename"] != parts[0]:
                        continue
                    node = f
                    for part in parts[1:]:
                        node = next((x for x in self._snapshot_files(tag, node["id"])
                                     if x["filename"] == part and x["directory"]), None)
                        if node is None:
                            break
                    if node is not None:
                        walk(node, d)
            elif any(fnmatch(f["filename"], pat) for pat in top_patterns):
                fetch(f, f["filename"])

    def _list_subjects(self):
        subs = sorted(p.name[4:] for p in self._root.glob("sub-*") if p.is_dir())
        return [s for s in subs if self._ieeg_files(s)]

    _EXT = (".vhdr", ".edf", ".set", ".fif", ".nwb", ".bdf", ".mefd")

    def _ieeg_files(self, subject):
        pattern = f"sub-{subject}_*_ieeg.*"
        files = [f for f in self._root.glob(f"sub-{subject}/**/ieeg/{pattern}")
                 if f.suffix.lower() in self._EXT]
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
        if path.suffix.lower() == ".nwb":
            from .nwb import read_nwb_raw

            raw, _, _ = read_nwb_raw(path, channel_types=("ecog", "seeg", "ieeg"),
                                     max_seconds=self.max_seconds)
            self._apply_sidecars(raw, path, channels=False)
        elif path.suffix.lower() == ".mefd":
            raw = self._read_mef(path)
            self._apply_sidecars(raw, path)
        else:
            bp = BIDSPath(root=self._root, datatype="ieeg", suffix="ieeg",
                          extension=path.suffix, **{k: v for k, v in ent.items() if v})
            with mne.utils.use_log_level("error"):
                try:
                    try:
                        raw = read_raw_bids(bp, verbose=False, on_ch_mismatch="warn")
                    except TypeError:  # older mne-bids without the argument
                        raw = read_raw_bids(bp, verbose=False)
                except (IndexError, KeyError, ValueError) as err:
                    # mne-bids trips on empty events.tsv or odd sidecars: read the file directly
                    # and take channel types from channels.tsv when present
                    raw = self._read_plain(path, err)
        raw.load_data()
        if self.max_seconds is not None and raw.times[-1] > self.max_seconds:
            raw.crop(tmax=float(self.max_seconds), include_tmax=False)
        types_now = dict(zip(raw.ch_names, raw.get_channel_types()))
        keep = [ch for ch, t in types_now.items() if t in self.channel_types or t in ("stim", "misc")]
        if not any(types_now[ch] in self.channel_types for ch in keep):
            # some datasets type their intracranial channels as EEG (or DBS): take those instead
            fallback = [ch for ch, t in types_now.items() if t in ("eeg", "dbs", "ecog", "seeg")]
            if not fallback:
                raise ValueError(f"{path.name}: no intracranial channels (types {sorted(set(types_now.values()))})")
            keep = fallback + [ch for ch, t in types_now.items() if t in ("stim", "misc")]
            raw.set_channel_types({ch: "ecog" for ch in fallback}, verbose=False)
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

    def _read_plain(self, path, err):
        warnings.warn(f"{path.name}: mne-bids failed ({type(err).__name__}); reading the file directly")
        raw = mne.io.read_raw(path, preload=True, verbose=False)
        self._apply_sidecars(raw, path)
        return raw

    def _apply_sidecars(self, raw, path, channels=True, events=True):
        """Channel types and bad channels from ``*_channels.tsv``, annotations from ``*_events.tsv``."""
        import pandas as pd

        stem = path.name.split("_ieeg")[0]
        ch_tsv = list(path.parent.glob(stem + "_channels.tsv"))
        if channels and ch_tsv:
            df = pd.read_csv(ch_tsv[0], sep="\t")
            if "name" in df.columns and "type" in df.columns:
                mapping = {}
                for name, typ in zip(df["name"].astype(str), df["type"].astype(str).str.lower()):
                    if name in raw.ch_names and typ in ("ecog", "seeg", "dbs", "eeg", "misc", "stim"):
                        mapping[name] = typ
                    elif name in raw.ch_names and typ in ("ecg", "ekg", "emg", "eog", "trig", "audio", "other",
                                                          "ref", "eeg-ref"):
                        mapping[name] = "misc"
                if mapping:
                    raw.set_channel_types(mapping, verbose=False)
            if "status" in df.columns:
                raw.info["bads"] = [n for n, st in zip(df["name"].astype(str), df["status"].astype(str))
                                    if st == "bad" and n in raw.ch_names]
        ev = list(path.parent.glob(stem + "_events.tsv"))
        if events and ev:
            df = pd.read_csv(ev[0], sep="\t")
            if len(df) and "onset" in df.columns:
                col = self.event_column if self.event_column in df.columns else df.columns[-1]
                # ds004624 lists negative durations for some stimulation events: MNE refuses those
                dur = (pd.to_numeric(df["duration"], errors="coerce").fillna(0.0).clip(lower=0.0)
                       if "duration" in df.columns else 0.0)
                onset = pd.to_numeric(df["onset"], errors="coerce")
                keep = onset.notna()
                if keep.any():
                    raw.set_annotations(mne.Annotations(onset[keep].astype(float),
                                                        dur[keep] if hasattr(dur, "__len__") else dur,
                                                        df[col][keep].astype(str)))
        return raw

    def _read_mef(self, path):
        """Read a MEF3 session directory (``*.mefd``) with pymef into a RawArray in volts.

        pymef returns the stored integers; ``units_conversion_factor`` (often negative, i.e. inverted
        polarity) and ``units_description`` turn them into volts. Discontinuities come back as NaN and are
        zeroed. Only the first ``max_seconds`` are read when set, which keeps hour-long CCEP sessions
        (ds003708: 89 channels at 2048 Hz) within a few hundred MB.
        """
        try:
            from pymef.mef_session import MefSession
        except ImportError as err:
            raise NotImplementedError("MEF3 (.mefd) needs pymef: pip install pymef") from err
        try:
            ms = MefSession(str(path), self.mef_password)
        except Exception as err:  # noqa: BLE001
            raise NotImplementedError(f"MEF3 session {path.name} could not be opened "
                                      f"({type(err).__name__}: {err}); encrypted?") from err

        def field(rec, key, default=None):
            try:
                v = rec[key]
            except (KeyError, ValueError, IndexError, TypeError):
                return default
            if hasattr(v, "size") and v.size == 1:
                v = v.item()
            return v.decode() if isinstance(v, bytes) else v

        md = ms.session_md
        s2 = md["time_series_metadata"]["section_2"]
        sfreq = float(field(s2, "sampling_frequency"))
        n_total = int(field(s2, "number_of_samples"))
        chans = md["time_series_channels"]
        names = list(chans)
        n = n_total if self.max_seconds is None else min(n_total, int(self.max_seconds * sfreq))
        data = np.zeros((len(names), n))
        for i, name in enumerate(names):
            cs2 = chans[name]["section_2"]
            ucf = float(field(cs2, "units_conversion_factor", 1.0) or 1.0)
            units = str(field(cs2, "units_description", "microvolts") or "microvolts").lower()
            scale = 1e-6 if "micro" in units else (1e-3 if "milli" in units else 1.0)
            x = np.asarray(ms.read_ts_channels_sample([name], [[0, n]])[0], dtype=float)
            m = min(x.size, n)
            data[i, :m] = np.nan_to_num(x[:m]) * ucf * scale
        info = mne.create_info(names, sfreq, ["ecog"] * len(names))
        raw = mne.io.RawArray(data, info, verbose=False)
        raw.info["description"] = f"MEF3 {path.name}"
        return raw

    def _get_single_subject_data(self, subject):
        out = {}
        files = self._ieeg_files(subject)
        if not files:
            raise FileNotFoundError(f"sub-{subject}: no readable ieeg files under {self._root}")
        if self.max_runs is not None:
            by_ses = {}
            for f in files:
                m = re.search(r"_ses-([A-Za-z0-9]+)_", f.name)
                by_ses.setdefault(m.group(1) if m else "0", []).append(f)
            files = [f for fs in by_ses.values() for f in fs[: int(self.max_runs)]]
        for f in files:
            raw, ent = self._load_file(f)
            session = ent["session"] or "0"
            run = "_".join(x for x in (ent["task"], ent["run"], ent["acquisition"]) if x) or "0"
            out.setdefault(session, {})[run] = raw
        raws = [r for runs in out.values() for r in runs.values()]
        # runs recorded with disjoint montages (monopolar vs bipolar exports, re-implantation) cannot
        # be pooled: keep the montage family with the most runs (ties: most channels), drop the rest
        if len(raws) > 1:
            families = {}
            for ses, runs in out.items():
                for run, r in runs.items():
                    key = frozenset(r.ch_names)
                    best = None
                    for fk in families:
                        if len(fk & key) >= 0.5 * min(len(fk), len(key)):
                            best = fk
                            break
                    families.setdefault(best if best is not None else key, []).append((ses, run))
            if len(families) > 1:
                import warnings

                keep_fam = max(families, key=lambda k: (len(families[k]), len(k)))
                dropped = [sr for fk, srs in families.items() if fk != keep_fam for sr in srs]
                warnings.warn(f"{self.code}: {len(dropped)} run(s) use a different montage and were dropped: "
                              f"{dropped[:4]}")
                for ses, run in dropped:
                    out[ses].pop(run)
                out = {ses: runs for ses, runs in out.items() if runs}
                raws = [r for runs in out.values() for r in runs.values()]
        # runs of one subject may differ in rejected channels: keep the common channels and give
        # every run the same channel types (a channel typed ECoG in any run is ECoG everywhere)
        if len(raws) > 1:
            common = set(raws[0].ch_names)
            for r in raws[1:]:
                common &= set(r.ch_names)
            for r in raws:
                keep = [ch for ch in r.ch_names if ch in common]
                if len(keep) < len(r.ch_names):
                    r.pick(keep)
            ecog = set()
            for r in raws:
                ecog |= {ch for ch, t in zip(r.ch_names, r.get_channel_types()) if t == "ecog"}
            for r in raws:
                fix = {ch: "ecog" for ch, t in zip(r.ch_names, r.get_channel_types())
                       if ch in ecog and t != "ecog"}
                if fix:
                    r.set_channel_types(fix, verbose=False)
        # channels marked bad in any run (channels.tsv status) are dropped from every run
        bads = set()
        for r in raws:
            bads |= set(r.info["bads"])
        for r in raws:
            drop = [ch for ch in r.ch_names if ch in bads]
            if drop and len(drop) < len(r.ch_names):
                r.drop_channels(drop)
            r.info["bads"] = []
        self._dropped_bads = sorted(bads)
        if self._events is None:
            # discover labels from annotations
            current = self.event_id or {}
            for r in raws:
                for lab in sorted(set(r.annotations.description)):
                    if lab not in current:
                        current[lab] = len(current) + 1
            self.event_id = current or None
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
