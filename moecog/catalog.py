"""Registry of catalog entries with loader factories for smoke tests.

Every entry pairs a dataset from ``docs/dataset_catalog.md`` with a callable
that builds a MOECoG dataset object restricted to a small subset (one subject
or one file), so that ``scripts/smoke_test.py`` can download, load and score
it within minutes. Entries whose source needs an account or a data-use
agreement are listed with ``blocked`` set, so the smoke-test table records the
reason instead of silently skipping them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources
from typing import Callable

_ON_META = json.loads(resources.files("moecog.data").joinpath("openneuro_ieeg.json").read_text())
_ON_SUBJ = json.loads(resources.files("moecog.data").joinpath("openneuro_subjects.json").read_text())


@dataclass
class Entry:
    id: str
    title: str
    source: str
    build: Callable | None = None
    paradigm: Callable | None = None
    blocked: str | None = None
    notes: str = ""
    tags: tuple = field(default_factory=tuple)


ENTRIES: dict[str, Entry] = {}


def _add(entry: Entry):
    ENTRIES[entry.id] = entry
    return entry


# ---------------------------------------------------------------- OpenNeuro
_NO_TASK = ("rest", "sleep", "sws", "seizure", "ictal", "interictal", "acute", "es", "restcontrolpre",
            "ccep", "task-spesclin", "task-spesprop", "dcs", "lozhfo", "photicstim")


# datasets whose files OpenNeuro refuses to serve (HTTP 403 on every file URL and on the S3 mirror);
# probably embargoed or not yet exported to S3. Re-check occasionally with
# `curl -sI -L https://openneuro.org/crn/datasets/<id>/snapshots/<tag>/files/participants.tsv`.
_ON_LOCKED = {
    # ds006254 answers 403 to HEAD only; the loader now falls back to GET through the GraphQL file tree
    "ds007703": "the snapshot lists only sidecar files (channels, events), no ieeg recordings; OpenNeuro also "
                "refuses HEAD on every file (checked 2026-09-10)",
    "ds005592": "deleted by OpenNeuro as a duplicate of ds006107, which loads",
}


# smoke subsets narrower than "first subject, everything": longitudinal sets where one subject spans
# hundreds of sessions (ds006890: two macaques, 127 daily sessions each, 22 GB per animal).
_ON_INCLUDE = {
    "ds006890": ["sub-monkeyc/ses-day05/*", "sub-monkeyc/ses-day06/*"],  # pressing + rest, rest + SEP
}


def _openneuro_entry(meta):
    did = meta["id"]
    subj = _ON_SUBJ.get(did, {})
    subjects = subj.get("subjects") or []
    tasks = subj.get("tasks") or meta.get("tasks") or []
    first = subjects[0] if subjects else None
    include = None
    if first:
        include = _ON_INCLUDE.get(did, [f"sub-{first}/*"]) + ["*.json", "*.tsv", "README*", "CHANGES", "participants*"]
    n_sub = len(subjects) or meta.get("n_subjects") or 0
    epoched = any(t.lower() not in _NO_TASK for t in tasks) if tasks else False

    def build(did=did, include=include, first=first):
        from moecog.datasets.bids import BIDSiEEGDataset

        return BIDSiEEGDataset(openneuro_id=did, include=include, subjects=[first] if first else None,
                               channel_types=("ecog", "seeg"), interval=[0.0, 1.0],
                               paradigm="epoched" if epoched else "rest", code=did)

    def paradigm():
        from moecog.paradigms import EpochedClassification

        return EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=150.0, resample=250.0)

    notes = f"{n_sub} subjects; tasks {','.join(tasks[:4])}; {(meta.get('size') or 0) / 1e9:.1f} GB"
    if did in _ON_LOCKED:
        notes += f"; BLOCKED: {_ON_LOCKED[did]}"
    return Entry(id=did, title=(meta.get("name") or did).strip()[:90] or did, source="openneuro", build=build,
                 paradigm=paradigm if epoched else None, blocked=did in _ON_LOCKED, notes=notes, tags=("bids",))


for _m in _ON_META:
    _add(_openneuro_entry(_m))

# ---------------------------------------------------------------- DANDI (NWB)
_DANDI = [
    ("000019", "Bouchard/Chang CV syllables (sub-EC9 B15)", r"sub-EC9_ses-EC9-B15", 1.0, "speech"),
    ("001193", "Shao IFG syntax/semantics high gamma", None, 0.1, "language"),
    ("000623", "Keles/Rutishauser movie watching (CS62)", r"sub-CS62_ses-P62CSR2", 1.0, "naturalistic"),
    ("000574", "Rutishauser verbal WM + iEEG (sub-05 ses-01)", r"sub-05_ses-01", 1.5, "memory"),
    ("000576", "Rutishauser amygdala aversive stimuli", None, 0.05, "visual"),
    ("000055", "AJILE12 (sub-04 ses-3)", r"sub-04_ses-3", 9.0, "naturalistic"),
]
for _d, _t, _inc, _gb, _tag in _DANDI:
    def _build(d=_d, inc=_inc, gb=_gb):
        from moecog.datasets.nwb import DANDIDataset

        return DANDIDataset(d, include=inc, max_asset_gb=gb, max_seconds=600.0, interval=[0.0, 1.0],
                            paradigm="nwb")

    def _par():
        from moecog.paradigms import EpochedClassification

        return EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=150.0, resample=250.0)

    _add(Entry(id=f"dandi-{_d}", title=_t, source="dandi", build=_build, paradigm=_par, tags=(_tag,)))

for _d, _t in [("000469", "Rutishauser Sternberg WM"), ("000004", "Rutishauser declarative memory"),
               ("001616", "SUMMER movie single-neuron")]:
    _add(Entry(id=f"dandi-{_d}", title=_t, source="dandi",
               blocked="single-unit spike times only; no field potentials or voltage in the NWB files (verified "
                       "2026-09-10 by opening the files)"))
_add(Entry(id="dandi-000571", title="Mayo CorTec BrainInterchange (MEF3)", source="dandi",
           blocked="MEF3 stored as .mefd directory trees on DANDI; pymef reader exists for BIDS, a DANDI folder "
                   "fetcher is still to write"))
_add(Entry(id="dandi-001638", title="Cogan µECoG pseudoword repetition", source="dandi",
           blocked="dandiset has no assets yet (empty on 2026-09-09)"))
_add(Entry(id="dandi-001613", title="Nentwich/Parra movies + eye tracking", source="dandi",
           blocked="only stimulus videos uploaded so far; no NWB assets"))

# ---------------------------------------------------------------- Miller library (validated)
for _exp in ["motor_basic", "imagery_basic", "faces_basic", "fingerflex", "visual_search", "memory_nback",
             "gestures", "imagery_feedback", "faces_noise", "speech_basic", "speech_lists",
             "joystick_track", "mouse_track", "fixation_PAC", "fixation_pwrlaw", "fixation_highfreq"]:
    def _bm(exp=_exp):
        from moecog.datasets import MillerLibrary

        ds = MillerLibrary(exp, download=False)
        ds.subject_list = ds.subject_list[:1]
        return ds

    def _pm(exp=_exp):
        from moecog.paradigms import EpochedClassification

        return EpochedClassification(tmin=0.0, tmax=None, fmin=1.0, fmax=200.0)

    _add(Entry(id=f"miller-{_exp}", title=f"Miller library {_exp}", source="miller", build=_bm,
               paradigm=_pm if _exp not in ("fingerflex", "joystick_track", "mouse_track", "fixation_PAC",
                                             "fixation_pwrlaw", "fixation_highfreq") else None,
               notes="needs MOECOG_MILLER_DIR"))

# ---------------------------------------------------------------- other public sources
def _misc(name, **kw):
    def build():
        import moecog.datasets.misc as misc

        return getattr(misc, name)(**kw)
    return build


def _epoched_par():
    from moecog.paradigms import EpochedClassification

    return EpochedClassification(tmin=0.0, tmax=None, fmin=1.0, fmax=150.0)


_add(Entry(id="dandi-001535", title="Natraj/Ganguly long-term ECoG BCI, BRAVO1 neural features (DANDI 001535)",
           source="dandi", build=_misc("BRAVOFeatures", max_trials=1500), paradigm=_epoched_par,
           notes="4.7 GB NWB; 9737 BCI trials of 256 neural features (high-gamma + low-frequency streams of a 128-ch "
                 "array) at 200 Hz, labelled by target_id; no raw voltage in the deposit", tags=("bci", "features")))
_add(Entry(id="bci-iv-4", title="BCI Competition IV dataset 4 (finger flexion)", source="bbci",
           build=_misc("BCICompIV4"), tags=("motor_regression",),
           notes="from the Miller SDR deposit BCI_Competion4_dataset4_data_fingerflexions"))
_add(Entry(id="bci-iii-1", title="BCI Competition III dataset I (ECoG motor imagery)", source="bbci",
           build=_misc("BCICompIII1"), paradigm=_epoched_par, tags=("motor_imagery",)))
_add(Entry(id="peterson-moverest", title="Peterson naturalistic move vs rest (EC09)", source="figshare",
           build=_misc("PetersonMoveRest", subjects=["EC09"]), paradigm=_epoched_par, tags=("naturalistic",)))
_add(Entry(id="peterson-reach", title="Peterson naturalistic reach epochs (subj 01 day 3)", source="figshare",
           build=_misc("PetersonReach", subjects=["01"]), tags=("naturalistic",)))
_add(Entry(id="peterson-pose", title="Peterson ECoG + arm pose (EC02)", source="figshare",
           build=_misc("PetersonPose", subjects=["EC02"]), tags=("naturalistic",)))
_add(Entry(id="rogers-uecog", title="Rogers submillimeter µECoG windows (S2)", source="figshare",
           build=_misc("RogersMicroECoG", subjects=["S2"]), tags=("uecog",)))
_add(Entry(id="verwoert-speech", title="Verwoert single-word production sEEG (iBIDS)", source="osf",
           build=_misc("VerwoertSpeech"), paradigm=_epoched_par, tags=("speech",)))
_add(Entry(id="merk-gripforce", title="Merk grip-force ECoG + STN (Dataverse)", source="dataverse",
           build=_misc("MerkGripForce"), tags=("motor_regression",)))
_add(Entry(id="duin", title="Du-IN Mandarin word sEEG (sub 001 run 1)", source="huggingface",
           build=_misc("DuIN", subjects=["001"], runs=[1]), paradigm=_epoched_par, tags=("speech",)))
_add(Entry(id="swec", title="SWEC long-term iEEG (ID01 part 1)", source="huggingface",
           build=_misc("SWEC", subjects=["ID01"], parts=[1]), tags=("clinical",)))
_add(Entry(id="omni-edf", title="Omni-iEEG raw EDF (Pt1)", source="huggingface",
           build=_misc("OmniEDF", files=["Pt1_AR_original_mne_griddep_10min.edf"]), tags=("clinical",)))
_add(Entry(id="mindeye-ieeg", title="mindeye iEEG NSD high-frequency broadband", source="huggingface",
           build=_misc("MindEyeIEEG"), tags=("visual",),
           notes="12 GB derivative array; loader reads shape only unless the array is present"))
_add(Entry(id="braintreebank", title="Brain Treebank (sub_1 trial000)", source="braintreebank",
           build=_misc("BrainTreebank", subjects=["1"], trials=[0]), tags=("naturalistic",)))
_add(Entry(id="stolk-sensorimotor", title="Stolk sensorimotor alpha/beta, high-density ECoG (OSF z4hfm)",
           source="osf", build=_misc("StolkSensorimotor", subjects=("S5",)),
           paradigm=_epoched_par,
           notes="3 patients, 120-ch grids, 49 cued-movement trials each (-1.5..2.5 s, 512 Hz); classes = "
                 "trialinfo condition code (undocumented in the deposit); 140/38/137 MB", tags=("motor",)))
_add(Entry(id="bellier-music", title="Bellier music reconstruction HFA, 29 patients (Zenodo 7876019)",
           source="zenodo", build=_misc("BellierMusic", subjects=("P1",)),
           notes="CC-BY; 70-150 Hz envelopes at 100 Hz, 190.7 s of song per patient; 32-band spectrogram as misc "
                 "target channels; regression paradigm to come; ~400 MB for all 29", tags=("auditory", "features")))


def _tonal():
    from moecog.datasets.scidb import TonalSpeechECoG

    return TonalSpeechECoG(subjects=("01",), sessions=("01",))


_add(Entry(id="tonal-speech", title="Li tonal speech perception ECoG, 4 awake-craniotomy patients (ScienceDB 27618)",
           source="scidb", build=_tonal,
           notes="CC-BY-4.0, 6.1 GB, 346 files; BIDS-iEEG with NWB recordings (128-256-ch grids, high gamma at 400 Hz "
                 "in derivatives); sentence listening (ASCCD corpus); 6 sessions per patient; downloads through "
                 "the ScienceDB file API", tags=("auditory", "speech")))

# ---------------------------------------------------------------- needs account / agreement
for _i, _t, _why in [
    ("cogitate", "Cogitate iEEG release 1", "portal registration + terms"),
    ("dabi-*", "DABI public projects (MGH stimulation/conversation, UTSW motor, Sheth, Beauchamp)",
     "DABI account required to download"),
    ("ebrains-*", "EBRAINS memory+pupillometry, EEG+stimulation", "EBRAINS account"),
    ("kaggle-seizure", "UPenn/Mayo and Melbourne seizure competitions", "Kaggle API token + competition rules"),
    ("mni-atlas", "MNI Open iEEG Atlas", "HTTP 401: registration"),
    ("neurotycho", "Neurotycho macaque ECoG", "download list behind registration (expdatalist)"),
    ("ieeg-org", "iEEG.org", "account"),
    ("crcns", "CRCNS ECoG/LFP sets", "account"),
    ("epilepsiae", "EPILEPSIAE", "restricted"),
    ("metzger-2023", "Chang lab neuroprosthesis deposit (Zenodo restricted)", "restricted deposit; request"),
    ("gin-usz", "GIN USZ intraoperative HFO", "duplicate of ds004944, which loads; no separate loader needed"),
]:
    _add(Entry(id=_i, title=_t, source="blocked", blocked=_why))


def summary():
    src = {}
    for e in ENTRIES.values():
        src.setdefault(e.source, [0, 0])
        src[e.source][0] += 1
        src[e.source][1] += int(bool(e.blocked))
    return src


__all__ = ["ENTRIES", "Entry", "summary"]
