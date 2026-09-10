# MOECoG — Mother of All ECoG Benchmarks

A MOABB-style benchmarking framework for electrocorticographic (ECoG) motor decoding.

> *"ECoG isn't just the future — it's the testable present."*

## Vision

[MOABB](https://github.com/NeuroTechX/moabb) transformed EEG-BCI research by making algorithm comparison reproducible and fair. **MOECoG does the same for ECoG motor decoding** — the signal modality at the critical intersection of clinical viability (long-term stability, lower surgical risk) and high-performance neural control (high-gamma access, mm-scale spatial resolution).

This project will be successful when we read in an abstract:

> *"...the proposed method obtained a correlation of 0.82 on MOECoG, outperforming the state of the art by 12%..."*

## Why ECoG Needs Its Own Benchmark

| Property | EEG (MOABB) | ECoG (MOECoG) |
|---|---|---|
| Signal type | Scalp potentials | Cortical surface potentials |
| Key features | mu/beta ERD/ERS | High-gamma broadband (>70 Hz) + beta suppression |
| Spatial resolution | ~cm | ~mm |
| Electrode geometry | Standard montages (10-20) | Patient-specific grids/strips |
| Primary tasks | Classification (L/R imagery) | Both classification AND continuous regression |
| Cross-subject | Standard channel alignment | Requires anatomical registration |
| Noise profile | EMG, EOG artifacts | Epileptiform activity, referencing |

MOABB's paradigm/dataset/evaluation/pipeline abstraction is brilliant — but its assumptions (fixed channel montages, epoched classification, standard frequency bands) break down for ECoG.

## Architecture

MOECoG follows MOABB's 4-concept design, adapted for ECoG:

```
+--------------+    +---------------+    +---------------+    +---------------+
|   Dataset    |--->|   Paradigm    |--->|  Evaluation   |--->|   Pipeline    |
|              |    |               |    |               |    |               |
| Raw ECoG +   |    | Motor Imagery |    | WithinSubject |    | Feature ext.  |
| electrode    |    | Finger Flex   |    | CrossSession  |    | + Classifier  |
| positions +  |    | Arm Reach     |    | Transfer      |    | or Regressor  |
| anatomy      |    | Grasp Type    |    |               |    |               |
+--------------+    +---------------+    +---------------+    +---------------+
```

### Key Differences from MOABB

- **Dual-task paradigms:** Classification (which finger?) AND regression (finger trajectory)
- **Anatomical electrode registration:** Patient-specific grids mapped to MNI/FreeSurfer atlas
- **Broadband feature extraction:** High-gamma (70-150 Hz), beta (13-30 Hz), phase-amplitude coupling
- **Continuous decoding metrics:** Correlation coefficient (r), R-squared, normalized MSE — not just accuracy
- **Naturalistic movement support:** Not just cued trials but free/spontaneous movements (AJILE12)

## Included Datasets

### Tier 1: Core Benchmark

Motor-specific, public, well-documented.

| ID | Dataset | Source | Subjects | Task | Channels | Modality |
|---|---|---|---|---|---|---|
| MillerFingerFlex | BCI Competition IV Dataset 4 | Miller & Schalk | 3 | Individual finger flexion (5-class regression) | 48-64 | ECoG grid |
| MillerLibrary | Stanford/Mayo ECoG Library | Miller 2019, *Nature Human Behaviour* | 34 | 16 experiments (motor, sensory, language, visual) | Varies | ECoG grid |
| AJILE12 | Annotated Joints in Long-term ECoG | Peterson et al. 2022, *Scientific Data* | 12 | Naturalistic wrist movements | >=64 | ECoG grid |

### Tier 2: Extended Benchmark

| ID | Dataset | Source | Subjects | Task |
|---|---|---|---|---|
| BCITetraplegia | BCI and Tetraplegia (WIMAGINE) | Benabid/Costecalde et al. | 1 (chronic) | 4-class motor imagery, 2D cursor |
| GraspECoG | Natural grasp types | Various (Pistohl, Bleichner) | Varies | Grasp classification |
| MoveAgain | Blackrock/BrainGate ECoG subsets | If released publicly | Varies | Arm/hand movement |

### Tier 3: Cross-Modality Comparison

| ID | Dataset | Why included |
|---|---|---|
| MOABB_MI | MOABB motor imagery EEG datasets | Direct EEG vs ECoG comparison on matched paradigms |

## Paradigms

### FingerFlexionRegression

- **Task:** Predict continuous finger flexion trajectories from ECoG
- **Metrics:** Pearson r, R-squared, NRMSE per finger
- **Datasets:** MillerFingerFlex, MillerLibrary (motor subset)
- **Baseline:** BCI Competition IV Dataset 4 leaderboard

### MotorImageryClassification

- **Task:** Classify imagined/attempted movements (L/R hand, feet, tongue, etc.)
- **Metrics:** Accuracy, ROC-AUC, Cohen's kappa
- **Datasets:** MillerLibrary (motor imagery subset), BCITetraplegia

### NaturalisticReachDecoding

- **Task:** Decode wrist movement onset and trajectory from unconstrained behavior
- **Metrics:** Event detection F1, trajectory r, latency
- **Datasets:** AJILE12

### GraspClassification

- **Task:** Classify grasp types or hand gestures from sensorimotor ECoG
- **Metrics:** Accuracy, confusion matrix analysis
- **Datasets:** GraspECoG, MillerLibrary (gesture subset)

## Evaluation Strategies

| Strategy | Description | Use Case |
|---|---|---|
| WithinSubjectCV | K-fold within single subject | Standard single-patient decoding |
| CrossSessionEval | Train on session A, test on session B | Stability / recalibration assessment |
| CrossSubjectTransfer | Leave-one-subject-out (with atlas projection) | Generalization / zero-shot transfer |
| TemporalStabilityEval | Chronological split (early to late) | Long-term signal stability |

## Baseline Pipelines

### Feature Extraction

- **LogBandPower** — Log power in canonical bands (mu, beta, low-gamma, high-gamma)
- **BroadbandChange** — Miller's broadband spectral change method
- **PAC** — Phase-amplitude coupling (theta/gamma, beta/high-gamma)
- **CSP_ECoG** — Common Spatial Patterns adapted for patient-specific grids
- **TimeFrequency** — Continuous wavelet / multitaper spectrograms

### Decoders

- **LDA / SVM / LogisticRegression** — Classical classifiers
- **Ridge / Kalman** — Linear regressors for trajectory decoding
- **ECoGNet** — Lightweight CNN for ECoG (braindecode-compatible)
- **FingerFlex** — Convolutional encoder-decoder (Lomtev et al.)
- **HTNet** — Transfer learning across subjects via Hilbert transform

## Status (2026-09-10)

| Layer | Implemented | Notes |
|---|---|---|
| Datasets | `MillerLibrary(experiment=...)` for all 16 Stanford/Miller experiments (204 files, 36 patients); `FakeECoGDataset` | Registry + data map in `docs/miller_library_map.md`; downloads from the Stanford Digital Repository with MD5 checks |
| Paradigms | `EpochedClassification` (+ `MotorClassification`, `FingerClassification`, `FaceHouseClassification`, `VisualSearchClassification`, `NBackTargetClassification`), `FingerFlexionRegression`, `CursorRegression` | Trials come from cue-code annotations; regression uses causal windows |
| Evaluations | `WithinSubjectCV` (chronological folds with purge for regression; contiguous or stratified-shuffled trial folds for classification) | Cross-session, cross-subject, temporal-stability still to do |
| Pipelines | `LogBandPower`, `HighGammaPower`; `classification_baselines()`, `regression_baselines()` | Deep decoders (braindecode, PACE zoo) still to do |
| Preprocessing | `CommonAverageReference`, `NotchFilter`, `HilbertEnvelope`, `chang_high_gamma()`; paradigms take `raw_steps=[...]` | Survey of the field's pipelines in `docs/preprocessing_catalog.md` |
| Other datasets | `BIDSiEEGDataset` (any BIDS-iEEG / OpenNeuro dataset, download via openneuro-py, `max_runs` memory guard) with named entries `HermesVisualECoG`, `PodcastECoG`, `FilmIEEG`, `VisualECoG` | Catalog of ~90 obtainable datasets in `docs/dataset_catalog.md` |
| Results | `results/*.csv` + `scripts/build_leaderboard.py` -> `docs/leaderboard.md` | first Miller baselines posted |
| Catalog registry | `moecog.catalog.ENTRIES` (130 entries: every OpenNeuro iEEG dataset with a one-subject subset, DANDI dandisets, Miller experiments, BCI competitions, figshare, OSF, Dataverse, Hugging Face, Brain Treebank, plus blocked entries with the access reason) | `scripts/smoke_test.py` downloads, loads and scores each entry; `docs/smoke_tests.md` is the outcome table (96 ok, 0 error, 12 unsupported, 22 blocked, 0 pending of 130 entries) |
| More loaders | `DANDIDataset`/`read_nwb_raw` (NWB), `BCICompIV4`, `BCICompIII1`, `PetersonMoveRest`/`PetersonReach`/`PetersonPose`, `RogersMicroECoG`, `VerwoertSpeech`, `MerkGripForce`, `DuIN`, `SWEC`, `OmniEDF`, `MindEyeIEEG`, `BrainTreebank` | datasets may deliver `mne.Epochs` instead of `Raw` |

Everything above is covered by `pytest -m "not slow"` on synthetic data; the
`slow` tests run against a local copy of the library
(`MOECOG_MILLER_DIR=/path/to/library pytest -m slow`).

## Quick Start

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from moecog.datasets import MillerLibrary
from moecog.evaluations import WithinSubjectCV
from moecog.paradigms import MotorClassification
from moecog.pipelines.features import HighGammaPower

# hand vs tongue movement, 19 patients of the Miller library (downloads ~850 MB once)
dataset = MillerLibrary("motor_basic")
paradigm = MotorClassification(fmin=1, fmax=200, tmax=3.0)
pipelines = {
    "HighGamma+LDA": make_pipeline(HighGammaPower(sfreq=1000.0), StandardScaler(),
                                   LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto"))
}
evaluation = WithinSubjectCV(paradigm=paradigm, datasets=[dataset], n_splits=5)
results = evaluation.process(pipelines, subjects=["bp", "jc"])
print(results[results.metric == "accuracy"].groupby(["subject", "pipeline"]).score.mean())
```

Continuous decoding uses the same four objects:

```python
from sklearn.linear_model import Ridge

from moecog.paradigms import FingerFlexionRegression
from moecog.pipelines.features import LogBandPower

dataset = MillerLibrary("fingerflex")
paradigm = FingerFlexionRegression(fmin=1, fmax=200, window_size=0.5, window_stride=0.05)
pipelines = {"LogBandPower+Ridge": make_pipeline(LogBandPower(sfreq=1000.0), Ridge(alpha=1.0))}
results = WithinSubjectCV(paradigm, [dataset], n_splits=5).process(pipelines, subjects=["bp"])
print(results[results.metric == "pearson_r"].score.mean())
```

Set `MOECOG_MILLER_DIR` to an existing extracted copy of the library to skip
the download (on FAU Athene: `/mnt/archive/home/yyu2024/PLaCT_data`).

## Installation

Data are cached under `$MOECOG_DATA_DIR` (default `~/moecog_data`).

```bash
pip install moecog
```

Or for development:

```bash
git clone https://github.com/epyifany/MOECoG.git
cd MOECoG
pip install -e ".[dev]"
```

### Dependencies

**Core:**
- `mne >= 1.5` — ECoG signal handling, coordinate transforms
- `numpy`, `scipy`, `scikit-learn` — Core ML
- `pandas` — Results management
- `h5py` — Persistent results storage
- `pooch` — Robust data downloading

**Optional:**
- `torch`, `braindecode` — Deep learning baselines (`pip install moecog[deep]`)
- `pynwb`, `dandi` — NWB data access for AJILE12 (`pip install moecog[nwb]`)
- `nilearn`, `nibabel` — Anatomical registration (`pip install moecog[anatomy]`)
- `matplotlib`, `seaborn` — Visualization (`pip install moecog[viz]`)

## Citation

If you use MOECoG in your research, please cite:

```bibtex
@software{moecog2025,
  title = {MOECoG: Mother of All ECoG Benchmarks},
  author = {Yu, Yifan},
  year = {2025},
  url = {https://github.com/epyifany/MOECoG}
}
```

And the foundational datasets:

- Miller, K.J. "A library of human electrocorticographic data and analyses." *Nature Human Behaviour* 3(11), 1225-1235 (2019).
- Peterson, S.M. et al. "AJILE12: Long-term naturalistic human intracranial neural recordings and pose." *Scientific Data* 9, 184 (2022).
- Schalk, G. et al. BCI Competition IV Dataset 4.

## License

BSD-3-Clause (matching MOABB)
