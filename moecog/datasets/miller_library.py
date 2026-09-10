"""Loader for the Stanford/Miller ECoG library (Miller, 2019).

"A library of human electrocorticographic data and analyses", Nature Human
Behaviour 3, 1225-1235 (2019). 204 recordings, 34 patients, 16 experiments,
all sampled at 1000 Hz (10 kHz for ``fixation_highfreq``) with a 0.15-200 Hz
one-pole analog band-pass. Public download: https://purl.stanford.edu/zk881ps0522

Where the trials live
---------------------
Every experiment ships one ``.mat`` file per patient (and per task or run).
Each file holds the ECoG matrix ``data`` (time x channels, amplifier units,
1 unit = 0.0298 microvolts) and, for the cued experiments, a **sample-wise code
channel** (``stim``, ``StimulusCode``, ``TargetCode`` or ``cues``) that holds
the screen cue at every sample. A trial is a contiguous block of a constant
code; Miller's own scripts catalogue trials exactly this way. Continuous
experiments carry their targets as extra time x k matrices (``flex``, ``dg``,
``CursorPosX``...). The top-level ``ns_1k_1_300_filt.mat`` in several folders is
the amplifier roll-off curve, not data. See ``docs/miller_library_map.md`` for
the per-experiment map that this registry encodes.

Every file is exposed as an :class:`mne.io.Raw` with

* ``ecog`` channels ``E001..Enn`` (scaled to volts),
* a ``stim`` channel ``STI`` holding the raw cue code per sample,
* ``misc`` channels for behavioural traces (``flex_thumb``, ``dg_index``,
  ``CursorPosX``, ``task``, ``coherence``...),
* :class:`mne.Annotations` named after the cue (``hand``, ``tongue``, ``face``,
  ``house``...) so that paradigms can epoch with ``mne.events_from_annotations``.

Data location
-------------
``MillerLibrary(root=...)`` or the environment variable ``MOECOG_MILLER_DIR``
point at a directory holding the extracted experiment folders
(``<root>/motor_basic/data/...``). Otherwise ``$MOECOG_DATA_DIR/miller2019``
(default ``~/moecog_data/miller2019``) is used and missing experiments are
downloaded from the Stanford Digital Repository with ``pooch`` (MD5-verified).
"""

from __future__ import annotations

import glob
import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import mne
import numpy as np
import scipy.io

from .base import BaseECoGDataset, ElectrodeInfo

MILLER_DOI = "10.1038/s41562-019-0678-3"
STANFORD_BASE_URL = "https://stacks.stanford.edu/file/druid:zk881ps0522"
AMPLIFIER_UNIT_VOLTS = 0.0298e-6  # 1 amplifier unit = 0.0298 microvolts

# MD5 checksums of the Stanford Digital Repository zips (verified 2026-07-16).
MILLER_ZIP_MD5 = {
    "faces_basic.zip": "812d92b2be0de466ba6c6683b53ea7f8",
    "faces_noise.zip": "89271b2993b09c804f78b43fe92b47b0",
    "fingerflex.zip": "8e44fef2a12ef42868b01a031f5b6350",
    "fixation_PAC.zip": "53bb098991aae4bb3cccc8e7544ac7ff",
    "fixation_highfreq.zip": "9ef3ae01bd10fa318fabe7f1671ba039",
    "fixation_pwrlaw.zip": "6c9c00009eb38f2fd9d04c6575dd6663",
    "gestures.zip": "30de1a74cab10feb2c13e0591df31462",
    "imagery_basic.zip": "38981b0a728ab96b42f65ff784e197ef",
    "imagery_feedback.zip": "dbf271d4b18becc0a354a718073ce5a0",
    "joystick_track.zip": "08c54cfaffae83ccbd3ec5dbdeeb2382",
    "memory_nback.zip": "408e98090a93c9f0ee58ac07c0b5a339",
    "motor_basic.zip": "cf87d50299b950ba251cf210217bb0aa",
    "mouse_track.zip": "28fa00d57f89ec1a289292c8362faf25",
    "speech_basic.zip": "3b7c52b532dbea4d7a98bfd0ce2576ca",
    "speech_lists.zip": "5557d752a26ecfe4ca6a649e9ccdfb7c",
    "visual_search.zip": "2a85384b8fe58e850d0bf724d08109d1",
}

# Miller's anatomical region codes (fingerflex ``elec_regions``, fixation_PAC
# ``el_codes``).
MILLER_REGION_CODES = {
    1: "dorsal_M1",
    3: "dorsal_S1",
    4: "ventral_sensorimotor",
    6: "frontal",
    7: "parietal",
    8: "temporal",
    9: "occipital",
}

FINGERS = ("thumb", "index", "middle", "ring", "little")
FINGER_EVENTS = {f: i + 1 for i, f in enumerate(FINGERS)}

# BCI2000 StimulusCode values used by the cue-based movement/imagery files.
# 13 (patient gf, motor_basic) is not documented in Miller's notes; 16 is
# inferred from the file name ``jc_mot_l_mov`` (``_l`` = hip movement).
CUE_CODES = {
    11: "tongue",
    12: "hand",
    13: "code_13",
    15: "say_move",
    16: "hip",
    19: "shrug",
}


def _range_map(ranges: dict[str, tuple[int, int]], isi_codes=()) -> Callable:
    """Map raw codes to class codes: ``{"house": (1, 50), "face": (51, 100)}``."""
    names = list(ranges)

    def fn(codes: np.ndarray, mat: dict) -> np.ndarray:
        out = np.zeros_like(codes)
        for i, name in enumerate(names):
            lo, hi = ranges[name]
            out[(codes >= lo) & (codes <= hi)] = i + 1
        for c in isi_codes:
            out[codes == c] = 0
        return out

    fn.events = {name: i + 1 for i, name in enumerate(names)}
    return fn


def _fhnoisy_map(codes: np.ndarray, mat: dict) -> np.ndarray:
    """faces_noise ``fhnoisy``: stim is the trial index (1-630); class in tr_fh."""
    tr_fh = np.asarray(mat["tr_fh"]).ravel().astype(int)  # 1 house, 2 face
    out = np.zeros_like(codes)
    m = codes > 0
    out[m] = tr_fh[codes[m] - 1]
    return out


_fhnoisy_map.events = {"house": 1, "face": 2}


def _fhnoisy_coherence(mat: dict) -> np.ndarray:
    """Per-sample noise level (0-100 %) of the stimulus on screen."""
    codes = np.asarray(mat["stim"]).ravel().astype(int)
    coh = np.asarray(mat["tr_coh"]).ravel().astype(float)
    out = np.full(codes.shape, np.nan)
    m = codes > 0
    out[m] = coh[codes[m] - 1]
    return out


def _nonzero_map(name: str) -> Callable:
    """Any nonzero code -> one class (speech cues, word ids)."""

    def fn(codes: np.ndarray, mat: dict) -> np.ndarray:
        return (codes > 0).astype(codes.dtype)

    fn.events = {name: 1}
    return fn


def _visual_search_map(codes: np.ndarray, mat: dict) -> np.ndarray:
    """1-10 right, 11-20 left, 21-30 down, 31-40 up, 41 ISI (Miller's vispac_master.m)."""
    out = np.zeros_like(codes)
    m = (codes >= 1) & (codes <= 40)
    out[m] = (codes[m] - 1) // 10 + 1
    return out


_visual_search_map.events = {"right": 1, "left": 2, "down": 3, "up": 4}


def _grasp_map(codes: np.ndarray, mat: dict) -> np.ndarray:
    """gestures glovefingersgrasp: 6,8 pinch -> 6; 7,9 fist -> 7."""
    out = codes.copy()
    out[codes == 8] = 6
    out[codes == 9] = 7
    return out


_grasp_map.events = {**FINGER_EVENTS, "pinch": 6, "fist": 7}


@dataclass(frozen=True)
class RunSpec:
    """One ``.mat`` file of the library.

    Parameters
    ----------
    session, run : str
        MOABB-style identifiers. Sessions separate task conditions (for example
        overt movement vs imagery); runs are repetitions of the same condition.
    file : str
        Path relative to the experiment folder; ``{s}`` is the patient code.
    stim : str or None
        Variable holding the sample-wise cue code (None for continuous or rest).
    events : dict
        ``{name: code}`` after ``code_map`` has been applied.
    code_map : callable or None
        ``fn(codes, mat) -> codes`` remapping raw codes to class codes.
    misc : dict
        ``{variable: prefix}`` time x k matrices kept as ``misc`` channels.
    derived : dict
        ``{channel_name: fn(mat) -> (n_times,) array}`` extra misc channels.
    data : str
        Variable holding the ECoG matrix.
    stim_file : str or None
        Separate file holding ``stim`` (fingerflex ``{s}_stim.mat``).
    """

    session: str
    run: str
    file: str
    stim: str | None = None
    events: dict[str, int] = field(default_factory=dict)
    code_map: Callable | None = None
    misc: dict[str, str] = field(default_factory=dict)
    derived: dict[str, Callable] = field(default_factory=dict)
    data: str = "data"
    stim_file: str | None = None


@dataclass(frozen=True)
class ExperimentSpec:
    """One of the 16 library experiments."""

    name: str
    paradigm: str
    runs: dict[str, tuple[RunSpec, ...]]  # patient -> files
    interval: list[float] | None
    locs: tuple[tuple[str, str, str], ...]  # (glob relative to experiment, variable, frame)
    sfreq: float = 1000.0
    region_var: tuple[str, str] | None = None  # (glob, variable) for region codes
    notes: str = ""

    @property
    def subjects(self) -> list[str]:
        return list(self.runs)

    @property
    def event_id(self) -> dict[str, int] | None:
        """Dataset-level ``{name: id}`` with one unique id per cue name.

        Per-file codes may clash across tasks (gestures reuses code 1 for
        "thumb", "pinch" and "gesture"), so ids are assigned by order of first
        appearance; annotations carry names, so the per-file codes never leak.
        """
        names: list[str] = []
        for specs in self.runs.values():
            for spec in specs:
                for k in spec.events:
                    if k not in names:
                        names.append(k)
        return {k: i + 1 for i, k in enumerate(names)} or None


def _uniform(subjects, session, run, file, **kw):
    """Same single file layout for every patient."""
    return {s: (RunSpec(session=session, run=run, file=file, **kw),) for s in subjects}


# ---------------------------------------------------------------------------
# Registry (encodes docs/miller_library_map.md; inventory taken 2026-09-09)
# ---------------------------------------------------------------------------

_MOTOR_TH = dict(stim="stim", events={"tongue": 11, "hand": 12})
_FEEDBACK_MISC = {"Cursor": "cursor", "Result": "result", "ITI": "iti"}

_GESTURE_TASKS = {
    "base": dict(),
    "fingerflex": dict(stim="stim", events=FINGER_EVENTS),
    "thumbfore": dict(stim="stim", events={"thumb": 1, "index": 2}),
    "pinch": dict(stim="stim", events={"pinch": 1}),
    "freeform": dict(stim="stim", events={"gesture": 1}),
    "rh_lh": dict(stim="stim", events={"right_hand": 5, "left_hand": 6, "both_hands": 7}),
    "mot_TH": dict(stim="stim", events={"tongue": 1, "hand": 2}),
    "glovefingersgrasp": dict(stim="stim", events=_grasp_map.events, code_map=_grasp_map),
}
_GESTURE_FILES = {
    "bp": ("base", "fingerflex", "freeform", "pinch", "rh_lh"),
    "ca": ("base", "fingerflex", "freeform", "mot_TH", "pinch"),
    "cc": ("base", "freeform", "pinch", "thumbfore"),
    "de": ("base", "freeform", "glovefingersgrasp"),
    "wm": ("base", "fingerflex", "freeform", "pinch", "thumbfore"),
}

_IMAGERY_FEEDBACK_FILES = {
    "al": ("fb_shrug", "im_ih_shrug", "mot_ih_shrug"),
    "fp": ("fbLR_hand", "fbUD_tongue", "im_t_h", "mot_t_h"),
    "hh": ("fb_tongue", "im_t", "mot_t"),
    "jc": ("fb_mov", "mot_l_mov"),
}


def _imagery_feedback_run(subject: str, task: str) -> RunSpec:
    file = f"data/{subject}/{subject}_{task}.mat"
    if task.startswith("fb"):
        return RunSpec(
            session=task, run="0", file=file, stim="TargetCode",
            events={"target_A": 1, "target_B": 2}, misc=_FEEDBACK_MISC,
        )
    codes = {"im_ih_shrug": (12, 19), "mot_ih_shrug": (12, 19), "im_t_h": (11, 12),
             "mot_t_h": (11, 12), "im_t": (11,), "mot_t": (11,), "mot_l_mov": (15, 16)}[task]
    events = {CUE_CODES[c]: c for c in codes}
    if "ih" in task:  # ipsilateral hand shares code 12 with (contralateral) hand
        events = {("hand_ipsi" if k == "hand" else k): v for k, v in events.items()}
    return RunSpec(session=task, run="0", file=file, stim="StimulusCode", events=events)


_FACES_MAP = _range_map({"house": (1, 50), "face": (51, 100)}, isi_codes=(101,))
_FACES_BASIC_SUBJECTS = ("aa", "ap", "ca", "de", "fp", "ha", "ja", "jm", "jt", "mv", "rn", "rr",
                         "wc", "zt")
_FACES_NOISE_SUBJECTS = ("ap", "ca", "ha", "ja", "mv", "wc", "zt")


def _faceshouses_run(subject: str) -> RunSpec:
    return RunSpec(
        session="faceshouses", run="0", file=f"data/{subject}/{subject}_faceshouses.mat",
        stim="stim", events=_FACES_MAP.events, code_map=_FACES_MAP,
    )


_SPEECH_BASIC_FILES = {
    "bp": ("verbs",), "hl": ("verbs",), "in": ("verbs",), "jc": ("nouns", "verbs"),
    "wc": ("nouns", "verbs"), "ww": ("nouns", "verbs"), "zt": ("nouns", "verbs"),
}
_SPEECH_EVENT = {"nouns": "read_noun", "verbs": "generate_verb"}


def _speech_lists_runs(subject: str) -> tuple[RunSpec, ...]:
    runs = []
    for lst in (1, 2):
        for kind in ("nouns", "verbs"):
            for r in (1, 2, 3):
                runs.append(RunSpec(
                    session=f"{kind}_L{lst}", run=f"R{r}",
                    file=f"data/{subject}/{subject}_{kind}_L{lst}_R{r}.mat",
                    stim="stim", events={_SPEECH_EVENT[kind]: 1},
                    code_map=_nonzero_map(_SPEECH_EVENT[kind]),
                ))
    if subject in ("jc", "wc"):
        runs.append(RunSpec(session="base", run="0", file=f"data/{subject}/{subject}_base.mat",
                            data="signal"))
    return tuple(runs)


_MOTOR_BASIC_SUBJECTS = ("bp", "ca", "cc", "de", "fp", "gc", "gf", "hh", "hl", "jc", "jf",
                         "jm", "jp", "jt", "rh", "rr", "ug", "wc", "zt")
_MOTOR_BASIC_EXTRA = {"gf": {"code_13": 13}, "zt": {"say_move": 15}}
_FIX_PWRLAW_SUBJECTS = ("al", "ca", "cc", "de", "fp", "gc", "gf", "gw", "h0", "hh", "jc", "jm",
                        "jp", "mv", "rh", "rr", "ug", "wc", "wm", "zt")

EXPERIMENTS: dict[str, ExperimentSpec] = {
    "fingerflex": ExperimentSpec(
        name="fingerflex", paradigm="motor_regression", interval=[0.0, 2.0],
        runs=_uniform(
            ("bp", "cc", "ht", "jc", "jp", "mv", "wc", "wm", "zt"), "0", "fingerflex",
            "data/{s}/{s}_fingerflex.mat", stim="stim", stim_file="data/{s}/{s}_stim.mat",
            events=FINGER_EVENTS, misc={"flex": "flex", "cue": "cue"},
        ),
        locs=(("data/{s}/{s}_fingerflex.mat", "locs", "native"),),
        region_var=("data/{s}/{s}_fingerflex.mat", "elec_regions"),
        notes="2 s cued finger movements, 30 per finger, 2 s rest between; flex = dataglove "
              "(40 ms blocks). {s}_stim.mat holds movement-aligned epochs, cue the screen cue.",
    ),
    "joystick_track": ExperimentSpec(
        name="joystick_track", paradigm="cursor_regression", interval=None,
        runs=_uniform(("fp", "gf", "rh", "rr"), "0", "joystick", "data/{s}_joystick.mat",
                      misc={"CursorPosX": "CursorPosX", "CursorPosY": "CursorPosY",
                            "TargetPosX": "TargetPosX", "TargetPosY": "TargetPosY"}),
        locs=(("data/{s}_joystick.mat", "electrodes", "talairach"),),
        notes="Continuous 2-D joystick tracking of a target moving on a circle (Schalk 2007).",
    ),
    "mouse_track": ExperimentSpec(
        name="mouse_track", paradigm="cursor_regression", interval=None,
        runs=_uniform(("fp", "gf", "rh", "rr"), "0", "mouse", "data/{s}_mouse.mat",
                      misc={"CursorPosX": "CursorPosX", "CursorPosY": "CursorPosY",
                            "TargetPosX": "TargetPosX", "TargetPosY": "TargetPosY"}),
        locs=(("data/{s}_mouse.mat", "electrodes", "talairach"),),
        notes="Continuous 2-D mouse tracking; same layout as joystick_track.",
    ),
    "motor_basic": ExperimentSpec(
        name="motor_basic", paradigm="motor_execution", interval=[0.0, 3.0],
        runs={s: (RunSpec(session="0", run="mot_t_h", file=f"data/{s}_mot_t_h.mat", stim="stim",
                          events={**_MOTOR_TH["events"], **_MOTOR_BASIC_EXTRA.get(s, {})},
                          misc={"dg": "dg"} if s == "jp" else {}),)
              for s in _MOTOR_BASIC_SUBJECTS},
        locs=(("locs/{s}_electrodes.mat", "electrodes", "talairach"),),
        notes="3 s cued hand (fist) or tongue movement blocks, ~30 per class (cc 15, jp 18/20, "
              "ug 45, jf 2 s blocks), 3 s rest between. gf has an undocumented code 13; zt has "
              "code 15 (say 'move').",
    ),
    "imagery_basic": ExperimentSpec(
        name="imagery_basic", paradigm="motor_imagery", interval=[0.0, 3.0],
        runs={s: (RunSpec(session="mot", run="0", file=f"data/{s}_mot_t_h.mat", **_MOTOR_TH),
                  RunSpec(session="im", run="0", file=f"data/{s}_im_t_h.mat", **_MOTOR_TH))
              for s in ("bp", "fp", "hh", "jc", "jm", "rh", "rr")},
        locs=(("locs/{s}_electrodes.mat", "electrodes", "talairach"),),
        notes="Session 'mot' = overt hand/tongue movement, 'im' = kinesthetic imagery of the "
              "same; 3 s cues, 30 per class per session.",
    ),
    "imagery_feedback": ExperimentSpec(
        name="imagery_feedback", paradigm="motor_imagery", interval=[0.0, 3.0],
        runs={s: tuple(_imagery_feedback_run(s, t) for t in tasks)
              for s, tasks in _IMAGERY_FEEDBACK_FILES.items()},
        locs=(("locs/{s}_locs_*.mat", "electrodes", "talairach"),),
        notes="Per patient: overt movement, imagery, and imagery-based 1-D cursor feedback "
              "(TargetCode A/B, variable-length trials, Cursor/Result/ITI as misc channels).",
    ),
    "gestures": ExperimentSpec(
        name="gestures", paradigm="motor_execution", interval=[0.0, 2.0],
        runs={s: tuple(RunSpec(session=t, run="0", file=f"data/{s}/{s}_{t}.mat",
                               misc={"dg": "dg"}, **_GESTURE_TASKS[t]) for t in tasks)
              for s, tasks in _GESTURE_FILES.items()},
        locs=(("locs/{s}_locs.mat", "locs", "talairach"),
              ("brains/{s}_*.mat", "locs", "native")),
        notes="Unpublished motor battery: 2 s cues (rh_lh and mot_TH 3 s), dataglove 'dg' in "
              "every file; task set differs per patient (see _GESTURE_FILES).",
    ),
    "faces_basic": ExperimentSpec(
        name="faces_basic", paradigm="visual", interval=[0.0, 0.4],
        runs={s: (_faceshouses_run(s),) for s in _FACES_BASIC_SUBJECTS},
        locs=(("locs/{s}_xslocs.mat", "locs", "voxel"),),
        region_var=("locs/{s}_xslocs.mat", "elcode"),
        notes="400 ms pictures of faces (codes 51-100) or houses (1-50), 150 each (rr 100), "
              "400 ms ISI (code 101). Electrode coordinates are MRI voxel indices.",
    ),
    "faces_noise": ExperimentSpec(
        name="faces_noise", paradigm="visual", interval=[0.0, 1.0],
        runs={s: (_faceshouses_run(s),
                  RunSpec(session="fhnoisy", run="0", file=f"data/{s}/{s}_fhnoisy.mat",
                          stim="stim", events=_fhnoisy_map.events, code_map=_fhnoisy_map,
                          misc={"key": "key"}, derived={"coherence": _fhnoisy_coherence}))
              for s in _FACES_NOISE_SUBJECTS},
        locs=(("locs/{s}_xslocs.mat", "locs", "voxel"),),
        region_var=("locs/{s}_xslocs.mat", "elcode"),
        notes="Session 'faceshouses' = localizer (as faces_basic); 'fhnoisy' = 630 one-second "
              "noise-masked faces/houses in 6 runs, noise level 0-100 % in 'coherence'.",
    ),
    "memory_nback": ExperimentSpec(
        name="memory_nback", paradigm="memory", interval=[0.0, 0.6],
        runs=_uniform(("al", "ca", "cc", "ug"), "0", "nback", "data/{s}_nback.mat",
                      stim="target", events={"nontarget": 1, "target": 2},
                      misc={"task": "task", "stim": "image", "response": "response"}),
        locs=(("locs/{s}_electrodes.mat", "electrodes", "talairach"),),
        notes="600 ms house pictures, 1.6 s ISI, 50 per run; 'task' misc channel = -1 baseline, "
              "0/1/2 = n-back level; 'image' = picture id 1-40. al: 150 stimuli, others 300.",
    ),
    "visual_search": ExperimentSpec(
        name="visual_search", paradigm="visual", interval=[0.0, 2.0],
        runs=_uniform(("jm", "jt", "rn", "rr", "wc"), "0", "vissearch",
                      "data/{s}/{s}_vissearch.mat", stim="stim",
                      events=_visual_search_map.events, code_map=_visual_search_map),
        locs=(("data/{s}/{s}_vissearch.mat", "locs", "native"),),
        notes="2 s search arrays cueing an arrow direction (30 per direction), 2 s ISI (41). "
              "Data are already common-average referenced and restricted to occipital strips "
              "(7-24 channels).",
    ),
    "speech_basic": ExperimentSpec(
        name="speech_basic", paradigm="speech", interval=[0.0, 1.6],
        runs={s: tuple(RunSpec(session=k, run="0", file=f"data/{s}_{k}.mat", stim="cues",
                               events={_SPEECH_EVENT[k]: 1}) for k in kinds)
              for s, kinds in _SPEECH_BASIC_FILES.items()},
        locs=(("brains/{s}_brain.mat", "locs", "native"),),
        notes="Visual noun cues; 'nouns' = read aloud, 'verbs' = generate a verb. 1.6 s cue / "
              "1.6 s ISI, 40 cues (bp 6.4 s cues; hl 33; in 12). Audio not distributed.",
    ),
    "speech_lists": ExperimentSpec(
        name="speech_lists", paradigm="speech", interval=[0.0, 1.6],
        runs={s: _speech_lists_runs(s) for s in ("jc", "wc", "ww")},
        locs=(("brains/{s}_brain.mat", "locs", "native"),),
        notes="Two 40-word lists x {read, generate verb} x 3 runs = 12 runs in fixed order; "
              "STI keeps the word id (1-40).",
    ),
    "fixation_PAC": ExperimentSpec(
        name="fixation_PAC", paradigm="rest", interval=None,
        runs=_uniform(("bp", "cc", "hl", "jc", "jm", "jp", "ug", "wc", "wm", "zt"), "0", "base",
                      "data/{s}/{s}_base.mat"),
        locs=(("data/{s}/{s}_base.mat", "locs", "native"),),
        region_var=("data/{s}/{s}_base.mat", "el_codes"),
        notes="2-3 min eyes-open fixation; region codes in el_codes[:, 1].",
    ),
    "fixation_pwrlaw": ExperimentSpec(
        name="fixation_pwrlaw", paradigm="rest", interval=None,
        runs=_uniform(_FIX_PWRLAW_SUBJECTS, "0", "base", "data/{s}_base.mat"),
        locs=(("data/{s}_base.mat", "locs", "talairach"),),
        notes="2-3 min eyes-open fixation, 20 patients.",
    ),
    "fixation_highfreq": ExperimentSpec(
        name="fixation_highfreq", paradigm="rest", interval=None, sfreq=10000.0,
        runs=_uniform(("s1", "s2", "s3", "s4"), "0", "10kbase", "data/{s}_10kbase.mat"),
        locs=(),
        notes="2 min fixation at 10 kHz, 4x8 arrays, no electrode coordinates distributed.",
    ),
}


def _blocks(codes: np.ndarray):
    """Yield (start, end, code) for contiguous constant-code blocks."""
    change = np.flatnonzero(np.diff(codes) != 0) + 1
    starts = np.r_[0, change]
    ends = np.r_[change, len(codes)]
    for s, e in zip(starts, ends):
        yield int(s), int(e), int(codes[s])


def annotations_from_codes(codes, sfreq, code_to_name, include_rest=False):
    """Build :class:`mne.Annotations` from a sample-wise cue-code channel.

    Parameters
    ----------
    codes : array-like, shape (n_times,)
        Class code per sample; 0 = no cue.
    sfreq : float
    code_to_name : dict
        ``{code: name}``. Unknown nonzero codes become ``"code_<k>"``.
    include_rest : bool
        Also annotate the zero blocks as ``"rest"``.
    """
    codes = np.asarray(codes).ravel().astype(int)
    onsets, durations, descs = [], [], []
    for s, e, c in _blocks(codes):
        if c == 0 and not include_rest:
            continue
        onsets.append(s / sfreq)
        durations.append((e - s) / sfreq)
        descs.append("rest" if c == 0 else code_to_name.get(c, f"code_{c}"))
    return mne.Annotations(onsets, durations, descs)


def _loadmat(path):
    return scipy.io.loadmat(path, squeeze_me=False, struct_as_record=True)


def _misc_matrix(mat, var):
    x = np.asarray(mat[var], dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    return x


class MillerLibrary(BaseECoGDataset):
    """One experiment of the Stanford/Miller ECoG library.

    Parameters
    ----------
    experiment : str
        One of :data:`EXPERIMENTS` (``"motor_basic"``, ``"faces_basic"``...).
    root : str or Path or None
        Directory holding the extracted experiment folders. Defaults to
        ``$MOECOG_MILLER_DIR``, else ``$MOECOG_DATA_DIR/miller2019``, else
        ``~/moecog_data/miller2019``.
    download : bool
        Download and extract the experiment zip if it is missing.
    include_rest : bool
        Annotate inter-cue (code 0) blocks as ``"rest"`` and add ``"rest"``
        to ``event_id`` (for cue-vs-rest paradigms).
    scale : float
        Multiplier applied to the raw amplifier units to get volts.
    """

    def __init__(self, experiment="motor_basic", root=None, download=True,
                 include_rest=False, scale=AMPLIFIER_UNIT_VOLTS):
        if experiment not in EXPERIMENTS:
            raise ValueError(f"Unknown experiment {experiment!r}; choose from {list(EXPERIMENTS)}")
        self.spec = EXPERIMENTS[experiment]
        self.experiment = experiment
        self.download = download
        self.include_rest = include_rest
        self.scale = scale
        self._root = Path(root).expanduser() if root else None
        events = self.spec.event_id
        if include_rest and events is not None:
            events = {**events, "rest": 0}
        super().__init__(
            subjects=self.spec.subjects,
            sessions_per_subject=max(
                len({r.session for r in runs}) for runs in self.spec.runs.values()
            ),
            events=events,
            code=f"Miller2019-{experiment}",
            paradigm=self.spec.paradigm,
            interval=self.spec.interval,
            sfreq=self.spec.sfreq,
            doi=MILLER_DOI,
        )

    # -- locations ---------------------------------------------------------
    @property
    def root(self) -> Path:
        if self._root is not None:
            return self._root
        env = os.environ.get("MOECOG_MILLER_DIR")
        if env:
            return Path(env).expanduser()
        base = os.environ.get("MOECOG_DATA_DIR", "~/moecog_data")
        return Path(base).expanduser() / "miller2019"

    @property
    def experiment_dir(self) -> Path:
        return self.root / self.experiment

    def runs(self, subject) -> tuple[RunSpec, ...]:
        return self.spec.runs[subject]

    def _ensure_downloaded(self):
        if self.experiment_dir.is_dir():
            return
        if not self.download:
            raise FileNotFoundError(
                f"{self.experiment_dir} not found. Set root=/MOECOG_MILLER_DIR or download=True."
            )
        import pooch

        fname = f"{self.experiment}.zip"
        self.root.mkdir(parents=True, exist_ok=True)
        pooch.retrieve(
            url=f"{STANFORD_BASE_URL}/{fname}",
            known_hash=f"md5:{MILLER_ZIP_MD5[fname]}",
            fname=fname,
            path=self.root,
            processor=pooch.Unzip(extract_dir="."),
            progressbar=True,
        )
        if not self.experiment_dir.is_dir():
            raise FileNotFoundError(f"Extraction did not create {self.experiment_dir}")

    def data_path(self, subject):
        self._ensure_downloaded()
        paths = []
        for spec in self.runs(subject):
            p = self.experiment_dir / spec.file.format(s=subject)
            if not p.is_file():
                raise FileNotFoundError(f"Missing library file: {p}")
            paths.append(p)
            if spec.stim_file:
                paths.append(self.experiment_dir / spec.stim_file.format(s=subject))
        return paths

    # -- loading -----------------------------------------------------------
    def _load_run(self, subject, spec: RunSpec) -> mne.io.Raw:
        path = self.experiment_dir / spec.file.format(s=subject)
        mat = _loadmat(path)
        ecog = np.asarray(mat[spec.data], dtype=float).T * self.scale  # (n_ch, n_times)
        n_ch, n_times = ecog.shape
        sfreq = self.spec.sfreq

        ch_names = [f"E{i + 1:03d}" for i in range(n_ch)]
        ch_types = ["ecog"] * n_ch
        arrays = [ecog]
        annotations = None

        if spec.stim is not None:
            if spec.stim_file:
                stim_mat = _loadmat(self.experiment_dir / spec.stim_file.format(s=subject))
                raw_codes = np.asarray(stim_mat["stim"]).ravel().astype(int)
            else:
                raw_codes = np.asarray(mat[spec.stim]).ravel().astype(int)
            raw_codes = raw_codes[:n_times]
            codes = spec.code_map(raw_codes, mat) if spec.code_map else raw_codes
            ch_names.append("STI")
            ch_types.append("stim")
            arrays.append(raw_codes[None, :].astype(float))
            code_to_name = {v: k for k, v in spec.events.items()}
            annotations = annotations_from_codes(codes, sfreq, code_to_name, self.include_rest)

        for var, prefix in spec.misc.items():
            if var not in mat:
                continue
            x = _misc_matrix(mat, var)[:n_times]
            if x.shape[1] == len(FINGERS) and prefix in ("flex", "dg"):
                names = [f"{prefix}_{f}" for f in FINGERS]
            elif x.shape[1] == 1:
                names = [prefix]
            else:
                names = [f"{prefix}_{i}" for i in range(x.shape[1])]
            ch_names += names
            ch_types += ["misc"] * len(names)
            arrays.append(x.T)

        for name, fn in spec.derived.items():
            x = np.asarray(fn(mat), dtype=float).ravel()[:n_times]
            ch_names.append(name)
            ch_types.append("misc")
            arrays.append(x[None, :])

        info = mne.create_info(ch_names, sfreq=sfreq, ch_types=ch_types)
        info["description"] = f"Miller2019/{self.experiment}/{subject}/{spec.session}/{spec.run}"
        raw = mne.io.RawArray(np.vstack(arrays), info, verbose=False)
        if annotations is not None:
            raw.set_annotations(annotations)
        self._set_montage(raw, subject)
        return raw

    def _set_montage(self, raw, subject):
        try:
            einfo = self.get_electrode_info(subject)
        except FileNotFoundError:
            return
        if einfo.coord_frame not in ("talairach", "mni") or einfo.positions.shape[0] != len(
            mne.pick_types(raw.info, ecog=True)
        ):
            return
        ecog_names = [raw.ch_names[i] for i in mne.pick_types(raw.info, ecog=True)]
        ch_pos = {n: einfo.positions[i] / 1000.0 for i, n in enumerate(ecog_names)}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            montage = mne.channels.make_dig_montage(ch_pos=ch_pos, coord_frame="mni_tal")
            raw.set_montage(montage, on_missing="ignore", verbose=False)

    def _get_single_subject_data(self, subject):
        self._ensure_downloaded()
        out: dict[str, dict[str, mne.io.Raw]] = {}
        for spec in self.runs(subject):
            out.setdefault(spec.session, {})[spec.run] = self._load_run(subject, spec)
        return out

    # -- electrodes ----------------------------------------------------------
    def get_electrode_info(self, subject):
        self._ensure_downloaded()
        for pattern, var, frame in self.spec.locs:
            hits = sorted(glob.glob(str(self.experiment_dir / pattern.format(s=subject))))
            for h in hits:
                mat = _loadmat(h)
                if var not in mat:
                    continue
                pos = np.asarray(mat[var], dtype=float)
                if pos.ndim != 2 or pos.shape[1] != 3:
                    continue
                region = None
                if self.spec.region_var:
                    rpat, rvar = self.spec.region_var
                    rhits = sorted(glob.glob(str(self.experiment_dir / rpat.format(s=subject))))
                    if rhits:
                        rmat = _loadmat(rhits[0])
                        if rvar in rmat:
                            r = np.asarray(rmat[rvar])
                            r = r[:, -1] if r.ndim == 2 and r.shape[1] > 1 else r.ravel()
                            region = [int(v) for v in r]
                return ElectrodeInfo(
                    positions=pos,
                    labels=[f"E{i + 1:03d}" for i in range(pos.shape[0])],
                    coord_frame=frame,
                    region_code=region,
                )
        raise FileNotFoundError(
            f"No electrode coordinates for {subject!r} in {self.experiment!r}"
        )

    def __repr__(self):
        return (
            f"MillerLibrary(experiment={self.experiment!r}, subjects={len(self.subject_list)}, "
            f"paradigm={self.paradigm_type!r})"
        )
