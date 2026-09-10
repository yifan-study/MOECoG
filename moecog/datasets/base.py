"""Base class for all ECoG datasets."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class ElectrodeInfo:
    """Patient-specific electrode metadata.

    Parameters
    ----------
    positions : np.ndarray, shape (n_channels, 3)
        Electrode coordinates. The frame is given by ``coord_frame``.
    labels : list of str
        Channel names.
    coord_frame : str
        One of ``"mni"``, ``"talairach"``, ``"native"`` (patient surface space,
        mm), or ``"voxel"`` (indices into the patient's MRI volume).
    hemisphere : list of str or None
        Hemisphere per electrode ("L" or "R").
    lobe : list of str or None
        Anatomical lobe per electrode.
    gyrus : list of str or None
        Gyrus per electrode.
    brodmann_area : list of int or None
        Brodmann area per electrode.
    region_code : list of int or None
        Dataset-specific anatomical code per electrode (for example Miller's
        ``elec_regions``: 1 dorsal M1, 3 dorsal S1, 4 ventral sensorimotor,
        6 frontal, 7 parietal, 8 temporal, 9 occipital).
    grid_type : str
        Electrode array type: "grid", "strip", or "depth".
    spacing_mm : float
        Inter-electrode distance in millimeters.
    """

    positions: np.ndarray
    labels: list[str]
    coord_frame: str = "mni"
    hemisphere: list[str] | None = None
    lobe: list[str] | None = None
    gyrus: list[str] | None = None
    brodmann_area: list[int] | None = None
    region_code: list[int] | None = None
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
    subjects : list of int or str
        Available subject identifiers (MOABB uses integers; the Miller library
        uses two-letter patient codes).
    sessions_per_subject : int
        Number of recording sessions per subject.
    events : dict or None
        Mapping of event names to integer codes. None for pure regression or
        resting-state datasets.
    code : str
        Unique dataset identifier string.
    paradigm : str
        Paradigm family, for example "motor_execution", "motor_imagery",
        "motor_regression", "cursor_regression", "visual", "memory", "speech",
        "rest", or "naturalistic".
    interval : list of float or None
        Default epoch window [tmin, tmax] in seconds relative to trial onset.
        None for continuous data.
    sfreq : float
        Sampling frequency in Hz.
    doi : str or None
        DOI of the associated publication.
    """

    def __init__(
        self,
        subjects: list,
        sessions_per_subject: int,
        events: dict[str, int] | None,
        code: str,
        paradigm: str,
        interval: list[float] | None,
        sfreq: float,
        doi: str | None = None,
    ):
        self.subject_list = list(subjects)
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
        subjects : list or None
            Subject identifiers to load. If None, loads all subjects.

        Returns
        -------
        dict
            Nested dict: ``{subject: {session: {run: mne.io.Raw}}}``.
        """
        subjects = subjects if subjects is not None else self.subject_list
        data = {}
        for subject in subjects:
            if subject not in self.subject_list:
                raise ValueError(
                    f"Subject {subject!r} is not in dataset {self.code!r}; "
                    f"available: {self.subject_list}"
                )
            data[subject] = self._get_single_subject_data(subject)
        return data

    @abstractmethod
    def _get_single_subject_data(self, subject):
        """Load all sessions and runs for a single subject.

        Returns
        -------
        dict
            ``{session_id: {run_id: mne.io.Raw}}``.
        """

    @abstractmethod
    def data_path(self, subject):
        """Return local file paths for a subject's data, downloading if needed.

        Returns
        -------
        list of Path
            Local paths to the data files.
        """

    @abstractmethod
    def get_electrode_info(self, subject):
        """Return electrode metadata for a subject.

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
