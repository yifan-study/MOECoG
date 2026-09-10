"""ScienceDB (scidb.cn) deposits: the Li-lab tonal speech perception ECoG set.

ScienceDB's website is JavaScript-only, but two endpoints answer plain HTTP without an account:

* ``POST https://www.scidb.cn/api/gin-sdb-filetree/public/file/childrenFileListByPath`` with
  ``{"dataSetId", "version", "path", "lastIndex", "pageSize"}`` lists one directory of a dataset version
  (paths start with the version folder, e.g. ``/V5/<root folder>``); every entry carries an ``id``.
* ``GET https://download.scidb.cn/download?fileId=<id>`` streams that file.

The tonal-speech deposit (DOI 10.57760/sciencedb.27618, CC-BY-4.0, 6.1 GB, 346 files) is BIDS-iEEG with
NWB recordings, except that each session folder holds its files flat (``sub-01/ses-01/*.nwb``) instead of
under ``ieeg/``. The loader rebuilds the ``ieeg/`` level while downloading so that
:class:`~moecog.datasets.bids.BIDSiEEGDataset` reads the result unchanged.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from .bids import BIDSiEEGDataset
from .misc import _data_dir, _download

TREE_URL = "https://www.scidb.cn/api/gin-sdb-filetree/public/file/childrenFileListByPath"
DOWNLOAD_URL = "https://download.scidb.cn/download?fileId={id}"


def list_scidb_dir(dataset_id: str, version: str, path: str, page_size: int = 500):
    """Return the entries (dicts with fileName, path, size, dir, id) of one directory of a ScienceDB dataset."""
    out, last = [], 0
    while True:
        body = json.dumps({"dataSetId": dataset_id, "version": version, "path": path, "lastIndex": last,
                           "pageSize": page_size}).encode()
        req = urllib.request.Request(TREE_URL, data=body, headers={"Content-Type": "application/json",
                                                                   "User-Agent": "moecog/0.2"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.load(resp)
        if payload.get("code") != 20000:
            raise RuntimeError(f"ScienceDB {dataset_id} {path}: {payload.get('messageEn') or payload.get('message')}")
        items = payload.get("data") or []
        out.extend(items)
        if len(items) < page_size:
            return out
        last += len(items)


class TonalSpeechECoG(BIDSiEEGDataset):
    """Li-lab high-density ECoG during Mandarin sentence listening (ScienceDB 27618, 4 awake-craniotomy patients).

    Parameters
    ----------
    subjects : sequence of str
        BIDS subject labels ("01".."04").
    sessions : sequence of str or None
        Session labels to fetch ("01".."06"); None fetches every session of the chosen subjects.
    """

    DATASET_ID = "c4d82d65ad5c4db88d712e68e199b6aa"
    VERSION = "V5"
    ROOT_DIR = "ECoG_Tonal_Speech_Perception_dataset"

    def __init__(self, subjects=("01",), sessions=("01",), root=None, **kw):
        self._want_subjects = tuple(subjects)
        self._want_sessions = tuple(sessions) if sessions else None
        root = Path(root).expanduser() if root else _data_dir() / "scidb" / "tonal_speech"
        kw.setdefault("channel_types", ("ecog", "seeg"))
        kw.setdefault("code", "TonalSpeech-ScienceDB27618")
        kw.setdefault("paradigm", "auditory")
        super().__init__(root=root, subjects=list(subjects), **kw)

    # -- download ------------------------------------------------------------------
    def _remote(self, rel=""):
        return list_scidb_dir(self.DATASET_ID, self.VERSION, f"/{self.VERSION}/{self.ROOT_DIR}" + rel)

    def _fetch(self, item, dest: Path):
        if dest.is_file() and dest.stat().st_size == int(item["size"]):
            return dest
        return _download(DOWNLOAD_URL.format(id=item["id"]), dest, expected_size=int(item["size"]))

    def _ensure_downloaded(self):
        wanted = [f"sub-{s}" for s in self._want_subjects]
        if all((self._root / w).is_dir() and any((self._root / w).rglob("*_ieeg.nwb")) for w in wanted):
            return
        if not self.download:
            raise FileNotFoundError(f"No tonal-speech data at {self._root}")
        self._root.mkdir(parents=True, exist_ok=True)
        top = self._remote()
        for item in top:
            if not item["dir"]:
                self._fetch(item, self._root / item["fileName"])
        for sub in wanted:
            for item in self._remote(f"/{sub}"):
                if not item["dir"]:
                    self._fetch(item, self._root / sub / item["fileName"])
                    continue
                if item["fileName"] == "ieeg":  # subject-level electrodes and channels tables
                    for f in self._remote(f"/{sub}/ieeg"):
                        if not f["dir"]:
                            self._fetch(f, self._root / sub / "ieeg" / f["fileName"])
                elif item["fileName"].startswith("ses-"):
                    ses = item["fileName"][4:]
                    if self._want_sessions is not None and ses not in self._want_sessions:
                        continue
                    for f in self._remote(f"/{sub}/{item['fileName']}"):
                        if f["dir"]:
                            continue
                        # the deposit keeps session files flat; BIDS wants them under ieeg/
                        self._fetch(f, self._root / sub / item["fileName"] / "ieeg" / f["fileName"])
        if not (self._root / "dataset_description.json").is_file():
            (self._root / "dataset_description.json").write_text(
                '{"Name": "ECoG_Tonal_Speech_Perception", "BIDSVersion": "1.7.0"}')
