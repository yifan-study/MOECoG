#!/usr/bin/env python3
# ruff: noqa: E501
"""Build docs/decodable_datasets.md: every catalog entry with size, what was recorded, what can be decoded.

Joins four sources: the catalog registry (``moecog.catalog.ENTRIES``), the smoke-test records
(``results/smoke/*.json``: channels, sampling rate, duration, classes, quick kappa), the OpenNeuro metadata
snapshots (``docs/catalog/openneuro_ieeg.json``, ``moecog/data/openneuro_subjects.json``: subjects, tasks,
size, licence) and the curated decoding notes below (task family, target, label type, which of our decoders
apply). Run after every smoke sweep:

    python scripts/build_dataset_list.py --out docs/decodable_datasets.md --json docs/decodable_datasets.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

# ----------------------------------------------------------------------------------------------------------------
# Curated decoding notes. Keys: catalog entry id (or an OpenNeuro accession). Fields:
#   fam      task family: motor, speech, auditory, visual, memory, naturalistic, bci, clinical, stimulation,
#            rest_sleep, animal
#   target   what a decoder predicts
#   kind     regression | classification | continuous | none | pretraining
#   fit      which of our decoders apply: R = continuous regression (PACE finger/cursor line), C = trial
#            classification (TRACE line), S = speech/audio, P = pretraining / self-supervised only
#   mod      ECoG | sEEG | mixed | uECoG | features | LFP+ECoG
#   note     anything the table should say
# ----------------------------------------------------------------------------------------------------------------
CURATED = {
    # Miller library
    "miller-fingerflex": dict(fam="motor", mod="ECoG", target="dataglove flexion of 5 fingers", kind="regression",
                              fit="R", note="the PACE/TRACE benchmark; 9 patients; cue channel gives finger id too"),
    "miller-joystick_track": dict(fam="motor", mod="ECoG", target="joystick cursor position/velocity", kind="regression", fit="R"),
    "miller-mouse_track": dict(fam="motor", mod="ECoG", target="mouse cursor position/velocity", kind="regression", fit="R"),
    "miller-motor_basic": dict(fam="motor", mod="ECoG", target="hand vs tongue movement (cued)", kind="classification", fit="C",
                               note="19 patients; kappa 0.90 with band power + LDA"),
    "miller-imagery_basic": dict(fam="motor", mod="ECoG", target="overt vs imagined hand/tongue", kind="classification", fit="C"),
    "miller-imagery_feedback": dict(fam="bci", mod="ECoG", target="imagery-driven cursor feedback cue", kind="classification", fit="C"),
    "miller-gestures": dict(fam="motor", mod="ECoG", target="4 hand gestures (rock/paper/scissors + rest)", kind="classification", fit="C"),
    "miller-faces_basic": dict(fam="visual", mod="ECoG", target="face vs house images", kind="classification", fit="C"),
    "miller-faces_noise": dict(fam="visual", mod="ECoG", target="face/house at 21 noise levels", kind="classification", fit="C"),
    "miller-visual_search": dict(fam="visual", mod="ECoG", target="attended direction in visual search", kind="classification", fit="C"),
    "miller-memory_nback": dict(fam="memory", mod="ECoG", target="n-back target vs non-target", kind="classification", fit="C"),
    "miller-speech_basic": dict(fam="speech", mod="ECoG", target="cued speech vs rest / word class", kind="classification", fit="C S"),
    "miller-speech_lists": dict(fam="speech", mod="ECoG", target="word lists (overt reading)", kind="classification", fit="C S"),
    "miller-fixation_PAC": dict(fam="rest_sleep", mod="ECoG", target="none (fixation rest)", kind="pretraining", fit="P"),
    "miller-fixation_pwrlaw": dict(fam="rest_sleep", mod="ECoG", target="none (fixation rest)", kind="pretraining", fit="P"),
    "miller-fixation_highfreq": dict(fam="rest_sleep", mod="ECoG", target="none (fixation rest)", kind="pretraining", fit="P"),
    # competitions and motor sets
    "bci-iv-4": dict(fam="motor", mod="ECoG", target="finger flexion (5 fingers, dataglove)", kind="regression", fit="R",
                     note="fixed train/test split; winner r 0.46"),
    "bci-iii-1": dict(fam="motor", mod="ECoG", target="imagined pinky vs tongue", kind="classification", fit="C",
                      note="one patient, sessions a week apart"),
    "merk-gripforce": dict(fam="motor", mod="LFP+ECoG", target="grip force (continuous)", kind="regression", fit="R",
                           note="intraoperative Parkinson's; ECoG strips + STN LFP"),
    "peterson-moverest": dict(fam="naturalistic", mod="ECoG", target="move vs rest (video-derived wrist events)", kind="classification", fit="C"),
    "peterson-reach": dict(fam="naturalistic", mod="ECoG", target="reach events (epochs)", kind="classification", fit="C"),
    "peterson-pose": dict(fam="naturalistic", mod="ECoG", target="2-D arm pose trajectories", kind="regression", fit="R"),
    "dandi-000055": dict(fam="naturalistic", mod="ECoG", target="wrist movement events, pose, behavioural state (55 days)", kind="continuous", fit="R C P",
                         note="AJILE12; 846 GB, subset mode"),
    "dandi-001535": dict(fam="bci", mod="features", target="BCI target id (7 targets) from neural features", kind="classification", fit="C",
                         note="features only (high-gamma + low-frequency), no voltage"),
    "stolk-sensorimotor": dict(fam="motor", mod="ECoG", target="cued movement condition code", kind="classification", fit="C",
                               note="high-density grids; trialinfo semantics to confirm with the authors' code"),
    "ds006890": dict(fam="animal", mod="ECoG", target="button pressing, reaching, listening vs rest (macaque)", kind="classification", fit="C R"),
    "ds004127": dict(fam="animal", mod="uECoG", target="rat somatosensory stimulation", kind="classification", fit="C"),
    "rogers-uecog": dict(fam="rest_sleep", mod="uECoG", target="none (unlabeled 2 s windows)", kind="pretraining", fit="P"),
    # speech and auditory
    "dandi-000019": dict(fam="speech", mod="ECoG", target="consonant-vowel syllables (read aloud)", kind="classification", fit="C S",
                         note="256-ch vSMC grids, 4 patients"),
    "verwoert-speech": dict(fam="speech", mod="sEEG", target="100 Dutch words / audio spectrogram", kind="classification", fit="C S R",
                            note="events.tsv trial_type gives speech vs rest; word identity in the stimulus column"),
    "duin": dict(fam="speech", mod="sEEG", target="61 Mandarin words (read aloud)", kind="classification", fit="C S",
                 note="12 patients, 2 kHz; Du-IN reports about 62 % 61-way"),
    "tonal-speech": dict(fam="auditory", mod="ECoG", target="tone/syllable/word features of heard Mandarin", kind="continuous", fit="S R"),
    "bellier-music": dict(fam="auditory", mod="features", target="32-band song spectrogram from HFA", kind="regression", fit="R S",
                          note="preprocessed HFA at 100 Hz, 29 patients"),
    "ds005574": dict(fam="auditory", mod="mixed", target="linguistic features of a 30-min podcast (encoding/decoding)", kind="continuous", fit="S R P"),
    "ds003688": dict(fam="naturalistic", mod="mixed", target="audiovisual film features; rest", kind="continuous", fit="S R P"),
    "ds004703": dict(fam="auditory", mod="sEEG", target="natural speech (passive listening)", kind="continuous", fit="S R",
                     note="licence forbids ML training: check before use"),
    "ds004993": dict(fam="auditory", mod="mixed", target="TIMIT sentences, movie trailers", kind="continuous", fit="S R"),
    "ds006910": dict(fam="speech", mod="ECoG", target="auditory naming: question vs answer epochs", kind="classification", fit="C S",
                     note="121 paediatric patients; kappa 0.89 on the smoke subject"),
    "ds006234": dict(fam="speech", mod="ECoG", target="auditory naming events", kind="classification", fit="C S"),
    "ds005545": dict(fam="speech", mod="ECoG", target="auditory naming events", kind="classification", fit="C S"),
    "ds006914": dict(fam="speech", mod="ECoG", target="picture naming events", kind="classification", fit="C S"),
    "ds006233": dict(fam="speech", mod="ECoG", target="picture naming events", kind="classification", fit="C S"),
    "ds005007": dict(fam="speech", mod="ECoG", target="wh-question answering", kind="classification", fit="C S"),
    "ds004770": dict(fam="memory", mod="ECoG", target="visuospatial working-memory game events", kind="classification", fit="C"),
    "ds004859": dict(fam="memory", mod="ECoG", target="Stroop congruent vs incongruent", kind="classification", fit="C"),
    "ds005931": dict(fam="motor", mod="ECoG", target="visuomotor game events", kind="classification", fit="C"),
    "braintreebank": dict(fam="naturalistic", mod="sEEG", target="Neuroprobe tasks: speech vs non-speech, pitch, volume, sentence onset, faces", kind="classification", fit="C S P",
                          note="10 subjects, 43 h, 130 GB"),
    "mindeye-ieeg": dict(fam="visual", mod="features", target="NSD image identity/CLIP embedding from broadband", kind="regression", fit="R C"),
    # visual
    "ds004194": dict(fam="visual", mod="mixed", target="pRF stimuli, pattern/contrast conditions", kind="classification", fit="C"),
    "ds005953": dict(fam="visual", mod="ECoG", target="grating vs noise stimuli", kind="classification", fit="C"),
    "dandi-000576": dict(fam="visual", mod="sEEG", target="aversive vs neutral images", kind="classification", fit="C"),
    # memory (RAM and others)
    "ds004789": dict(fam="memory", mod="mixed", target="free recall: encoding events, recalled vs forgotten", kind="classification", fit="C P", note="RAM FR1, 280 patients"),
    "ds004809": dict(fam="memory", mod="mixed", target="categorised free recall events", kind="classification", fit="C P", note="RAM catFR1, 258 patients"),
    "ds005059": dict(fam="memory", mod="mixed", target="paired-associate learning events", kind="classification", fit="C", note="RAM PAL1"),
    "ds004865": dict(fam="memory", mod="mixed", target="free recall events", kind="classification", fit="C", note="RAM pyFR"),
    "ds005411": dict(fam="memory", mod="mixed", target="repeated free recall events", kind="classification", fit="C", note="RAM RepFR1"),
    "ds005522": dict(fam="memory", mod="mixed", target="spatial navigation: position log, object location memory", kind="continuous", fit="R C",
                     note="RAM YC1; events.tsv is a dense position log"),
    "ds005523": dict(fam="memory", mod="mixed", target="spatial navigation with stimulation", kind="continuous", fit="R C", note="RAM YC2"),
    "ds005489": dict(fam="stimulation", mod="mixed", target="free recall with open-loop stimulation", kind="classification", fit="C", note="RAM FR2"),
    "ds005491": dict(fam="stimulation", mod="mixed", target="categorised recall with stimulation", kind="classification", fit="C", note="RAM catFR2"),
    "ds005494": dict(fam="stimulation", mod="mixed", target="paired associates with stimulation", kind="classification", fit="C", note="RAM PAL2"),
    "ds005557": dict(fam="stimulation", mod="mixed", target="free recall, closed-loop stimulation", kind="classification", fit="C", note="RAM FR3"),
    "ds005558": dict(fam="stimulation", mod="mixed", target="categorised recall, closed-loop stimulation", kind="classification", fit="C", note="RAM catFR3"),
    "ds004752": dict(fam="memory", mod="mixed", target="Sternberg working-memory load", kind="classification", fit="C"),
    "ds006136": dict(fam="memory", mod="mixed", target="object working memory (load 3)", kind="classification", fit="C"),
    "ds005624": dict(fam="memory", mod="mixed", target="colour change detection", kind="classification", fit="C"),
    "ds005415": dict(fam="memory", mod="sEEG", target="symbolic vs non-symbolic numbers, auditory vs visual", kind="classification", fit="C"),
    "ds004473": dict(fam="memory", mod="sEEG", target="forced two-choice response", kind="classification", fit="C"),
    "dandi-000574": dict(fam="memory", mod="sEEG", target="verbal working-memory load", kind="classification", fit="C"),
    "dandi-000623": dict(fam="naturalistic", mod="sEEG", target="movie encoding vs recognition", kind="classification", fit="C P"),
    "dandi-001193": dict(fam="speech", mod="features", target="syntax/semantics conditions (IFG high gamma)", kind="classification", fit="C S"),
    # clinical, rest, sleep, stimulation (pretraining or clinical tier)
    "swec": dict(fam="clinical", mod="sEEG", target="seizure onset (long-term)", kind="classification", fit="P C", note="4.6 TB on Hugging Face; research-only licence"),
    "omni-edf": dict(fam="clinical", mod="mixed", target="HFO / spike / artefact labels", kind="classification", fit="C P"),
    "ds004944": dict(fam="clinical", mod="ECoG", target="HFO / epileptiform detection, pre vs post resection", kind="classification", fit="C P"),
    "ds003498": dict(fam="clinical", mod="mixed", target="interictal HFO annotations", kind="classification", fit="C P"),
    "ds007095": dict(fam="clinical", mod="ECoG", target="chronic RNS recordings", kind="pretraining", fit="P"),
    "ds003029": dict(fam="clinical", mod="mixed", target="ictal vs interictal, seizure onset zone", kind="classification", fit="C P"),
    "ds004100": dict(fam="clinical", mod="mixed", target="ictal vs interictal", kind="classification", fit="C P"),
    "ds003876": dict(fam="clinical", mod="mixed", target="interictal", kind="pretraining", fit="P"),
    "ds003844": dict(fam="clinical", mod="mixed", target="acute epilepsy monitoring", kind="pretraining", fit="P"),
    "ds003848": dict(fam="clinical", mod="mixed", target="long-term epilepsy monitoring", kind="pretraining", fit="P"),
    "ds004080": dict(fam="stimulation", mod="ECoG", target="CCEP responses to single-pulse stimulation", kind="classification", fit="C", note="74 patients, 289 GB"),
    "ds004774": dict(fam="stimulation", mod="ECoG", target="CCEP responses", kind="classification", fit="C", note="MEF3"),
    "ds005448": dict(fam="stimulation", mod="ECoG", target="CCEP responses", kind="classification", fit="C"),
    "ds004370": dict(fam="stimulation", mod="ECoG", target="CCEP responses", kind="classification", fit="C"),
    "ds004696": dict(fam="stimulation", mod="ECoG", target="CCEP responses", kind="classification", fit="C", note="MEF3"),
    "ds004977": dict(fam="stimulation", mod="ECoG", target="CCEP responses", kind="classification", fit="C", note="MEF3"),
    "ds003708": dict(fam="stimulation", mod="ECoG", target="CCEP responses", kind="classification", fit="C", note="MEF3"),
    "ds004457": dict(fam="stimulation", mod="mixed", target="CCEP responses", kind="classification", fit="C", note="MEF3"),
    "ds004624": dict(fam="stimulation", mod="ECoG", target="CorTec BrainInterchange recordings", kind="pretraining", fit="P", note="MEF3, intraoperative"),
    "ds006392": dict(fam="stimulation", mod="mixed", target="photic stimulation responses", kind="classification", fit="C", note="MEF3"),
    "ds006254": dict(fam="stimulation", mod="mixed", target="CCEP on anti-seizure medication", kind="classification", fit="C", note="files served with GET only"),
    "ds005398": dict(fam="rest_sleep", mod="ECoG", target="none (interictal sleep)", kind="pretraining", fit="P", note="185 paediatric patients"),
    "ds004551": dict(fam="rest_sleep", mod="ECoG", target="none (interictal sleep)", kind="pretraining", fit="P"),
    "ds006107": dict(fam="rest_sleep", mod="ECoG", target="none (interictal sleep)", kind="pretraining", fit="P"),
    "ds007118": dict(fam="rest_sleep", mod="ECoG", target="none (interictal sleep)", kind="pretraining", fit="P"),
    "ds007119": dict(fam="rest_sleep", mod="ECoG", target="none (interictal sleep)", kind="pretraining", fit="P"),
    "ds007120": dict(fam="rest_sleep", mod="ECoG", target="none (interictal sleep)", kind="pretraining", fit="P"),
    # entries the keyword guess cannot place
    "ds003078": dict(fam="clinical", mod="sEEG", target="none documented (PROBE clinical iEEG)", kind="pretraining", fit="P"),
    "ds008610": dict(fam="animal", mod="LFP+ECoG", target="focused-ultrasound vs tactile stimulation (NHP thalamus)", kind="classification", fit="C"),
    "ds005691": dict(fam="auditory", mod="sEEG", target="auditory deviant counting (oddball)", kind="classification", fit="C"),
    "ds004819": dict(fam="clinical", mod="sEEG", target="none (high channel-count electrode demonstration)", kind="pretraining", fit="P"),
    "ds006253": dict(fam="visual", mod="mixed", target="random-dot motion decision and confidence", kind="classification", fit="C", note="snapshot ships no recordings"),
    "ds005083": dict(fam="clinical", mod="sEEG", target="none (paediatric sEEG safety cohort)", kind="none", fit="", note="snapshot ships no recordings"),
    "ds005592": dict(fam="rest_sleep", mod="ECoG", target="none (interictal sleep)", kind="pretraining", fit="P", note="deleted duplicate of ds006107"),
    "dandi-000571": dict(fam="stimulation", mod="ECoG", target="CorTec BrainInterchange device recordings (BCI2000 tasks)", kind="classification", fit="C P", note="MEF3 folders on DANDI"),
    "cogitate": dict(fam="visual", mod="mixed", target="faces/objects/letters/false fonts, task relevance", kind="classification", fit="C", note="38 patients; registration"),
    "mni-atlas": dict(fam="rest_sleep", mod="mixed", target="none (normal wake/sleep iEEG atlas)", kind="pretraining", fit="P"),
    "neurotycho": dict(fam="animal", mod="ECoG", target="3-D reach kinematics (motion capture), visual gratings, sleep/anaesthesia", kind="regression", fit="R C P", note="macaque 128-ch; Chao 2010 r 0.7-0.8"),
    "ieeg-org": dict(fam="clinical", mod="mixed", target="seizures, clinical annotations", kind="classification", fit="C P"),
    "crcns": dict(fam="animal", mod="ECoG", target="auditory/visual stimulation (various species)", kind="classification", fit="C"),
    "dabi-*": dict(fam="stimulation", mod="mixed", target="single-pulse and theta-burst stimulation; UTSW motor tasks with DBS", kind="classification", fit="C R"),
    "ebrains-*": dict(fam="memory", mod="sEEG", target="memory tasks with pupillometry", kind="classification", fit="C"),
    "kaggle-seizure": dict(fam="clinical", mod="mixed", target="seizure detection / prediction (humans + dogs)", kind="classification", fit="C"),
    "epilepsiae": dict(fam="clinical", mod="mixed", target="long-term seizure recordings (275 patients)", kind="classification", fit="C P"),
    "metzger-2023": dict(fam="speech", mod="ECoG", target="sentences, phonemes, avatar (speech neuroprosthesis)", kind="classification", fit="C S", note="restricted Zenodo deposit"),
    "gin-usz": dict(fam="clinical", mod="ECoG", target="intraoperative HFO", kind="classification", fit="C", note="duplicate of ds004944"),
    "dandi-001638": dict(fam="speech", mod="uECoG", target="pseudoword repetition (Cogan lab)", kind="classification", fit="C S", note="no assets yet"),
    "dandi-001613": dict(fam="naturalistic", mod="sEEG", target="movies, images, eye tracking", kind="continuous", fit="C P", note="stimuli only so far"),
}

# deposit sizes (GB) for entries without OpenNeuro metadata; DANDI sizes come from docs/catalog/dandi_names.json
SIZE_GB = {
    "bci-iv-4": 0.22, "bci-iii-1": 0.05, "merk-gripforce": 1.4, "verwoert-speech": 2.8, "duin": 12.0,
    "peterson-moverest": 10.7, "peterson-reach": 17.0, "peterson-pose": 10.8, "rogers-uecog": 6.4,
    "braintreebank": 130.0, "swec": 4600.0, "omni-edf": 159.0, "mindeye-ieeg": 12.0, "bellier-music": 0.4,
    "stolk-sensorimotor": 0.32, "tonal-speech": 6.1, "neurotycho": 50.0, "cogitate": 300.0,
}
MILLER_TOTAL_GB = 7.5

# subject counts of deposits the smoke test only samples (the smoke record knows one subject)
SUBJECTS = {
    "stolk-sensorimotor": 3, "bellier-music": 29, "verwoert-speech": 10, "duin": 12, "bci-iii-1": 1, "bci-iv-4": 3,
    "merk-gripforce": 11, "peterson-moverest": 12, "peterson-reach": 12, "peterson-pose": 12, "rogers-uecog": 4,
    "braintreebank": 10, "dandi-000019": 4, "dandi-001535": 1, "dandi-000055": 12, "swec": 68, "omni-edf": 55,
    "mindeye-ieeg": 12, "dandi-000574": 21, "dandi-000623": 1, "dandi-000576": 9, "dandi-001193": 1,
    "tonal-speech": 4, "cogitate": 38, "neurotycho": 4, "mni-atlas": 106,
}

FAMILY_ORDER = ["motor", "bci", "speech", "auditory", "visual", "memory", "naturalistic", "animal", "stimulation",
                "clinical", "rest_sleep", "other"]
FAMILY_TITLE = {"motor": "Motor (movement, kinematics, force)", "bci": "Brain-computer interface control",
                "speech": "Speech production and naming", "auditory": "Auditory and language perception",
                "visual": "Visual stimuli", "memory": "Memory and cognition", "naturalistic": "Naturalistic, long-term",
                "animal": "Non-human", "stimulation": "Electrical stimulation (CCEP, closed loop)",
                "clinical": "Clinical (seizures, HFO, artefacts)", "rest_sleep": "Rest and sleep (unlabeled)",
                "other": "Other"}
FIT_TEXT = {"R": "regression (PACE/TRACE finger-flexion line)", "C": "trial classification",
            "S": "speech/audio decoding", "P": "pretraining / self-supervised"}


def _measured_modality(eid):
    """ECoG / sEEG channel shares from the channels.tsv files of a downloaded subset, when present."""
    import csv
    import glob
    import os

    root = os.environ.get("MOECOG_DATA_DIR") or os.path.expanduser("~/moecog_data")
    files = glob.glob(f"{root}/openneuro/{eid}/sub-*/**/ieeg/*_channels.tsv", recursive=True)
    if not files:
        return None
    ecog = seeg = total = 0
    for f in files[:8]:
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in csv.DictReader(fh, delimiter="\t"):
                t = (line.get("type") or "").upper()
                total += 1
                ecog += t == "ECOG"
                seeg += t in ("SEEG", "DBS")
    if not total:
        return None
    return round(100 * ecog / total), round(100 * seeg / total)


def _modality_label(ecog_pct, seeg_pct):
    if ecog_pct >= 80:
        return "ECoG"
    if seeg_pct >= 80:
        return "sEEG"
    if ecog_pct + seeg_pct < 40:
        return "unverified"  # channels typed EEG/other; the loader falls back to those
    return "mixed"


def _guess(entry, tasks):
    """Task family for entries without curated notes, from task names and titles."""
    text = " ".join([entry.title] + list(tasks) + list(entry.tags or ())).lower()
    if any(k in text for k in ("sleep", "rest", "sws", "interictal", "fixation")):
        return "rest_sleep", "none (rest/sleep)", "pretraining", "P"
    if any(k in text for k in ("seizure", "ictal", "hfo", "epilep", "rns")):
        return "clinical", "seizure / interictal events", "classification", "C P"
    if any(k in text for k in ("ccep", "stim", "spes", "dcs", "photic")):
        return "stimulation", "stimulation responses", "classification", "C"
    if any(k in text for k in ("speech", "naming", "word", "syllable", "listen", "podcast", "audio", "sentence")):
        return "speech", "speech or language events", "classification", "C S"
    if any(k in text for k in ("memory", "recall", "sternberg", "wm", "nback", "n-back")):
        return "memory", "memory task events", "classification", "C"
    if any(k in text for k in ("visual", "image", "face", "picture", "movie", "film", "video")):
        return "visual", "visual stimuli", "classification", "C"
    if any(k in text for k in ("motor", "finger", "hand", "reach", "grasp", "gesture", "move", "joystick", "cursor")):
        return "motor", "movement events", "classification", "C"
    return "other", "see task list", "classification", "C"


def _size_gb(entry, meta, dandi_sizes):
    m = meta.get(entry.id) or {}
    if m.get("size"):
        return m["size"] / 1e9
    if entry.id in SIZE_GB:
        return SIZE_GB[entry.id]
    if entry.id.startswith("dandi-") and entry.id[6:] in dandi_sizes:
        return dandi_sizes[entry.id[6:]] / 1e9
    note = entry.notes or ""
    mm = re.search(r"([\d.]+)\s*(GB|MB|TB)", note)
    if mm:
        v = float(mm.group(1))
        return v / 1e3 if mm.group(2) == "MB" else (v * 1e3 if mm.group(2) == "TB" else v)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/smoke")
    ap.add_argument("--out", default="docs/decodable_datasets.md")
    ap.add_argument("--json", default="docs/decodable_datasets.json")
    args = ap.parse_args()
    from moecog.catalog import ENTRIES

    root = Path(__file__).resolve().parents[1]
    smoke = {f.stem: json.loads(f.read_text()) for f in Path(args.results).glob("*.json")}
    on_meta = {m["id"]: m for m in json.loads((root / "docs/catalog/openneuro_ieeg.json").read_text())}
    on_subj = json.loads((root / "moecog/data/openneuro_subjects.json").read_text())
    dandi_sizes = {d["id"]: d.get("size") or 0 for d in json.loads((root / "docs/catalog/dandi_names.json").read_text())}
    from moecog.datasets.miller_library import EXPERIMENTS

    miller_patients = {f"miller-{k}": len(v.runs) for k, v in EXPERIMENTS.items()}
    rows = []
    for eid, e in ENTRIES.items():
        r = smoke.get(eid) or {}
        meta = on_meta.get(eid, {})
        subj = on_subj.get(eid, {})
        tasks = subj.get("tasks") or meta.get("tasks") or []
        cur = CURATED.get(eid)
        if cur:
            fam, target, kind, fit = cur["fam"], cur["target"], cur["kind"], cur["fit"]
            mod, note = cur.get("mod", ""), cur.get("note", "")
        else:
            fam, target, kind, fit = _guess(e, tasks)
            mod, note = "", ""
        if e.blocked:
            status = "blocked"
        else:
            status = r.get("status", "pending")
        ses = r.get("sessions") or {}
        first = next(iter(ses.values()), {}) if ses else {}
        n_sub = (len(subj.get("subjects") or []) or meta.get("n_subjects") or miller_patients.get(eid)
                 or SUBJECTS.get(eid) or r.get("subjects_found") or "")
        if eid.startswith("miller-") and not note:
            note = f"part of the 7.5 GB Miller library ({miller_patients.get(eid)} patients)"
        qb = r.get("quick_baseline") or {}
        score = qb.get("score")
        kappa = "" if score is None or score != score else f"{score:.2f}"
        mod_source = "curated" if cur and cur.get("mod") else "guess"
        ecog_pct = seeg_pct = None
        if eid.startswith("ds"):
            measured = _measured_modality(eid)
            if measured:
                ecog_pct, seeg_pct = measured
                mod, mod_source = _modality_label(ecog_pct, seeg_pct), "channels.tsv"
        if not mod:
            mod = "unverified" if eid.startswith("ds") else "ECoG"
        rows.append({
            "id": eid, "title": e.title, "source": e.source, "family": fam, "modality": mod,
            "modality_source": mod_source, "ecog_pct": ecog_pct, "seeg_pct": seeg_pct,
            "n_subjects": n_sub, "channels": first.get("n_ecog", ""), "sfreq": first.get("sfreq", ""),
            "duration_s": first.get("duration_s", ""), "size_gb": _size_gb(e, on_meta, dandi_sizes),
            "licence": meta.get("license", ""), "tasks": ", ".join(str(t) for t in tasks[:5]),
            "target": target, "kind": kind, "fit": fit, "status": status, "quick_kappa": kappa,
            "classes": len(first.get("classes", {}) or {}), "electrodes": (r.get("electrodes") or {}).get("n", "")
            if isinstance(r.get("electrodes"), dict) else "",
            "note": note or (e.blocked if isinstance(e.blocked, str) else "") or "",
            "catalog_notes": e.notes or "",
        })
    rows.sort(key=lambda x: (FAMILY_ORDER.index(x["family"]) if x["family"] in FAMILY_ORDER else 99,
                             {"ok": 0, "unsupported": 1, "blocked": 2, "error": 3, "pending": 4}.get(x["status"], 9),
                             -(x["size_gb"] or 0)))
    Path(args.json).write_text(json.dumps(rows, indent=1))

    total_gb = sum(x["size_gb"] or 0 for x in rows)
    ok = [x for x in rows if x["status"] == "ok"]
    by_mod = {}
    for x in rows:
        b = by_mod.setdefault(x["modality"], [0, 0.0, 0])
        b[0] += 1
        b[1] += x["size_gb"] or 0
        b[2] += x["status"] == "ok"
    lines = [
        "# Decodable ECoG / iEEG datasets",
        "",
        f"Generated {dt.date.today().isoformat()} by `scripts/build_dataset_list.py` from the catalog registry, the smoke-test "
        "records and the OpenNeuro metadata snapshots. One row per catalog entry; channels, rate and duration are those of "
        "the first subject's first run as loaded by MOECoG (a subset, not the whole dataset). Sizes are the full deposits. "
        "'Fit' says which of our decoder lines apply: R = continuous regression (finger flexion, cursor, force, audio), "
        "C = trial classification, S = speech/audio decoding, P = pretraining / self-supervised only.",
        "",
        f"{len(rows)} entries, {len(ok)} load today, about {total_gb / 1e3:.1f} TB of public deposits in total "
        f"({sum((x['size_gb'] or 0) for x in ok) / 1e3:.1f} TB behind the entries that load).",
        "",
        "## Size by modality", "",
        "Not all of it is subdural ECoG. *modality* comes from the channel types in the downloaded subset's "
        "channels.tsv (ECoG = at least 80 % ECOG channels, sEEG = at least 80 % SEEG/DBS, mixed = both, unverified = "
        "channels typed EEG/other) where a subset is on this machine, otherwise from the curated notes; 'features' "
        "and 'µECoG' are curated.", "",
        "| modality | entries | load | total size |", "|---|---|---|---|",
    ] + [f"| {m} | {b[0]} | {b[2]} | {b[1] / 1e3:.2f} TB |"
         for m, b in sorted(by_mod.items(), key=lambda kv: -kv[1][1])] + [
        "",
        "One archive dominates the total: SWEC-ETHZ long-term clinical sEEG on Hugging Face (4.6 TB). The RAM memory "
        "sets (depth electrodes with some grids and strips, 1.5 TB across the family) and AJILE12 (0.85 TB of "
        "continuous subdural ECoG) are the next largest; the motor-decoding sets our regression line targets are "
        "small in bytes (the whole Miller library is 7.5 GB, BCI IV-4 is 220 MB).",
        "",
    ]
    for fam in FAMILY_ORDER:
        sub = [x for x in rows if x["family"] == fam]
        if not sub:
            continue
        lines += [f"## {FAMILY_TITLE[fam]} ({len(sub)})", "",
                  "| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for x in sub:
            run = ""
            if x["channels"] != "":
                run = f"{x['channels']} @ {float(x['sfreq']):.0f}, {float(x['duration_s']):.0f} s"
            size = "" if x["size_gb"] is None else (f"{x['size_gb'] * 1e3:.0f} MB" if x["size_gb"] < 1 else f"{x['size_gb']:.1f} GB")
            note = (x["note"] or "").replace("|", "/")
            mod_cell = x["modality"]
            if x.get("ecog_pct") is not None:
                mod_cell += f" ({x['ecog_pct']} % ECoG, {x['seeg_pct']} % sEEG)"
            lines.append(f"| {x['id']} | {x['title'][:70].replace('|', '/')} | {mod_cell} | {x['n_subjects']} | {run} | {size} | "
                         f"{x['licence']} | {x['target'].replace('|', '/')} | {x['kind']} | {x['fit']} | {x['status']} | {x['quick_kappa']} | {note} |")
        lines.append("")
    lines += ["## Reading the table", "",
              "- *kind*: regression = a continuous behavioural signal is recorded alongside (finger flexion, cursor, force, "
              "pose, audio spectrogram); classification = discrete trials with labels; continuous = naturalistic signal with "
              "time-aligned annotations (encoding/decoding both possible); pretraining = no behavioural labels.",
              "- *status*: ok = downloaded, loaded and (when a trial paradigm applies) scored by `scripts/smoke_test.py`; "
              "unsupported = the files hold no usable field potentials or use a format we cannot read yet; blocked = "
              "account, DUA or a repository problem (see `docs/dataset_catalog.md`).",
              "- *quick kappa*: LogBandPower + LDA, 3 chronological folds, one subject. A sanity check, not a benchmark.",
              ""]
    Path(args.out).write_text("\n".join(lines))
    fams = {}
    for x in rows:
        fams.setdefault(x["family"], []).append(x)
    print(f"wrote {args.out}: {len(rows)} rows; " + ", ".join(f"{k} {len(v)}" for k, v in fams.items()))


if __name__ == "__main__":
    main()
