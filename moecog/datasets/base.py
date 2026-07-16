"""Base class for all ECoG datasets."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class ElectrodeInfo:
    """Patient-specific electrode metadata.

    Parameters
    ----------
    positions : np.ndarray, shape (n_channels, 3)
        Electrode coordinates (MNI or native space).
    labels : list of str
        Channel names.
    hemisphere : list of str or None
        Hemisphere per electrode ("L" or "R").
    lobe : list of str or None
        Anatomical lobe per electrode.
    gyrus : list of str or None
        Gyrus per electrode.
    brodmann_area : list of int or None
        Brodmann area per electrode.
    grid_type : str
        Electrode array type: "grid", "strip", or "depth".
    spacing_mm : float
        Inter-electrode distance in millimeters.
    """

    positions: np.ndarray
    labels: list[str]
    hemisphere: list[str] | None = None
    lobe: list[str] | None = None
    gyrus: list[str] | None = None
    brodmann_area: list[int] | None = None
    grid_type: str = "grid"
    spacing_mm: float = 10.0


class BaseECoGDataset(ABC):
    """Base class for all ECoG datasets.

    Every concrete dataset must implement:
        - ``_get_single_subject_data(subject)``
        - ``data_path(subject)``
        - ``get_electrode_info(subject)``

    Parameters
    ----------
    subjects : list of int
        Available subject IDs.
    sessions_per_subject : int
        Number of recording sessions per subject.
    events : dict or None
        Mapping of event names to integer codes. None for pure regression datasets.
    code : str
        Unique dataset identifier string.
    paradigm : str
        Paradigm type: "motor_regression", "motor_imagery", or "naturalistic".
    interval : list of float or None
        Epoch window [tmin, tmax] in seconds. None for continuous data.
    sfreq : float
        Sampling frequency in Hz.
    doi : str or None
        DOI of the associated publication.
    """

    def __init__(
        self,
        subjects: list[int],
        sessions_per_subject: int,
        events: dict[str, int] | None,
        code: str,
        paradigm: str,
        interval: list[float] | None,
        sfreq: float,
        doi: str | None = None,
    ):
        self.subject_list = subjects
        self.n_sessions = sessions_per_subject
        self.event_id = events
        self.code = code
        self.paradigm_type = paradigm
        self.interval = interval
        self.sfreq = sfreq
        self.doi = doi

    def get_data(self, subjects=None):
        """Load data for one or more subjects.

        Parameters
        ----------
        subjects : list of int or None
            Subject IDs to load. If None, loads all subjects.

        Returns
        -------
        dict
            Nested dict: ``{subject: {session: {run: mne.io.Raw}}}``.
        """
        subjects = subjects or self.subject_list
        data = {}
        for subject in subjects:
            data[subject] = self._get_single_subject_data(subject)
        return data

    @abstractmethod
    def _get_single_subject_data(self, subject):
        """Load all sessions and runs for a single subject.

        Parameters
        ----------
        subject : int
            Subject identifier.

        Returns
        -------
        dict
            ``{session_id: {run_id: mne.io.Raw}}``.
        """

    @abstractmethod
    def data_path(self, subject):
        """Return local file paths for a subject's data, downloading if needed.

        Parameters
        ----------
        subject : int
            Subject identifier.

        Returns
        -------
        list of Path
            Local paths to the data files.
        """

    @abstractmethod
    def get_electrode_info(self, subject):
        """Return electrode metadata for a subject.

        Parameters
        ----------
        subject : int
            Subject identifier.

        Returns
        -------
        ElectrodeInfo
            Electrode positions and anatomical labels.
        """

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(code={self.code!r}, "
            f"subjects={len(self.subject_list)}, "
            f"sessions={self.n_sessions})"
        )
