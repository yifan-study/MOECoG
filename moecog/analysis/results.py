"""Results bookkeeping: one tidy CSV per store, rows keyed by digests so reruns skip what exists.

MOABB keeps an HDF5 file keyed by a hash of the pipeline's ``repr``; a cosmetic change reruns everything and the
file needs locks on shared filesystems. Here a row carries ``pipeline_digest`` (hash of the estimator's
``get_params``), ``paradigm_digest`` (hash of the paradigm's parameters), ``evaluation``, ``moecog_version`` and
``computed_at``, and the store is a plain CSV that git can diff.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pandas as pd

from .. import __version__

KEY_COLUMNS = ["dataset", "subject", "session", "pipeline", "pipeline_digest", "paradigm_digest", "evaluation"]


def _jsonable(value):
    if hasattr(value, "get_params"):
        return {"__class__": type(value).__name__, "params": _jsonable(value.get_params(deep=False))}
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    if hasattr(value, "tolist"):
        return value.tolist()
    return repr(value)


def digest(obj, n: int = 12) -> str:
    """Stable short hash of a JSON-able description of ``obj``."""
    payload = json.dumps(_jsonable(obj), sort_keys=True, default=repr).encode()
    return hashlib.sha1(payload).hexdigest()[:n]


def pipeline_digest(pipeline) -> str:
    """Hash of the pipeline's parameters (not its repr), so cosmetic changes do not invalidate results."""
    return digest(pipeline.get_params(deep=True) if hasattr(pipeline, "get_params") else pipeline)


def paradigm_digest(paradigm) -> str:
    """Hash of the paradigm class name and its public attributes."""
    attrs = {k: v for k, v in vars(paradigm).items() if not k.startswith("_")}
    return digest({"class": type(paradigm).__name__, "attrs": attrs})


class ResultsStore:
    """Append-only CSV of evaluation rows with digests, plus ``not_yet_computed`` queries.

    Parameters
    ----------
    path : str or Path
        CSV file; created on the first ``add``.
    overwrite : bool
        Ignore (and on the next ``add`` replace) an existing file.
    """

    def __init__(self, path, overwrite: bool = False):
        self.path = Path(path)
        self.overwrite = overwrite
        if self.path.is_file() and not overwrite:
            self.df = pd.read_csv(self.path)
        else:
            self.df = pd.DataFrame()

    # -- queries --------------------------------------------------------------------
    def _done(self, dataset_code, subject, session, pipeline_dig, paradigm_dig, evaluation) -> bool:
        if self.df.empty:
            return False
        d = self.df
        m = (d["dataset"] == dataset_code) & (d["subject"].astype(str) == str(subject)) \
            & (d["pipeline_digest"] == pipeline_dig) & (d["paradigm_digest"] == paradigm_dig) \
            & (d["evaluation"] == evaluation)
        if session is not None:
            m &= d["session"].astype(str) == str(session)
        return bool(m.any())

    def paradigm_mismatch(self, dataset_code: str, evaluation: str, paradigm) -> list:
        """Digests of other paradigms already stored for this (dataset, evaluation).

        A non-empty list means rows computed under a different paradigm (another sampling rate, band or
        epoch window) sit next to what is about to be computed; tables grouped by pipeline name would mix
        them. ``benchmark()`` warns on it.
        """
        if self.df.empty or "paradigm_digest" not in self.df.columns:
            return []
        d = self.df[(self.df["dataset"] == dataset_code) & (self.df["evaluation"] == evaluation)]
        others = set(d["paradigm_digest"].astype(str)) - {paradigm_digest(paradigm)}
        return sorted(others)

    def not_yet_computed(self, pipelines: dict, dataset_code: str, subject, paradigm, evaluation: str,
                         session=None) -> dict:
        """Subset of ``pipelines`` with no stored rows for this (dataset, subject[, session])."""
        pdig = paradigm_digest(paradigm)
        return {name: p for name, p in pipelines.items()
                if not self._done(dataset_code, subject, session, pipeline_digest(p), pdig, evaluation)}

    # -- writes ---------------------------------------------------------------------
    def add(self, rows, pipelines: dict, paradigm, evaluation: str, replace: bool = False) -> pd.DataFrame:
        """Append rows (list of dicts or DataFrame from an evaluation) and write the CSV.

        With ``replace=True`` the stored rows sharing (dataset, subject, session, pipeline, paradigm, evaluation)
        with the new ones are dropped first, so a recomputation replaces exactly what it recomputed.
        """
        new = pd.DataFrame(rows) if not isinstance(rows, pd.DataFrame) else rows.copy()
        if new.empty:
            return new
        digests = {name: pipeline_digest(p) for name, p in pipelines.items()}
        new["pipeline_digest"] = new["pipeline"].map(digests)
        new["paradigm_digest"] = paradigm_digest(paradigm)
        new["evaluation"] = evaluation
        new["moecog_version"] = __version__
        new["computed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._append(new, replace=replace)
        return new

    def merge_from(self, other, replace: bool = False) -> pd.DataFrame:
        """Bring the rows of another store (path or DataFrame) into this one and write the CSV.

        Rows are matched on (dataset, subject, session, pipeline_digest, paradigm_digest, evaluation): by default
        only combinations this store has not computed are added, with ``replace=True`` the incoming rows win.
        This is how results computed elsewhere (a cluster, a contributor's machine) join the repository's CSV
        without recomputing anything. Returns the rows that were added.
        """
        incoming = other.copy() if isinstance(other, pd.DataFrame) else pd.read_csv(other)
        if incoming.empty:
            return incoming
        missing = [k for k in self.KEYS if k not in incoming.columns]
        if missing:
            raise ValueError(f"cannot merge: incoming rows lack {missing}")
        if not replace and not self.df.empty:
            have = set(self._key_strings(self.df))
            incoming = incoming[~self._key_strings(incoming).isin(have)]
            if incoming.empty:
                return incoming
        self._append(incoming, replace=replace)
        return incoming

    KEYS = ("dataset", "subject", "session", "pipeline_digest", "paradigm_digest", "evaluation")

    @classmethod
    def _key_strings(cls, df: pd.DataFrame) -> pd.Series:
        return df[list(cls.KEYS)].astype(str).agg("|".join, axis=1)

    def _append(self, new: pd.DataFrame, replace: bool) -> None:
        if replace and not self.df.empty:
            new_keys = set(self._key_strings(new))
            self.df = self.df[~self._key_strings(self.df).isin(new_keys)]
        self.df = pd.concat([self.df, new], ignore_index=True) if not self.df.empty else new.reset_index(drop=True)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(self.path, index=False)
        self.overwrite = False

    def to_dataframe(self) -> pd.DataFrame:
        return self.df.copy()
