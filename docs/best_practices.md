# What the field does: preprocessing, transfer and evaluation for ECoG decoding

A literature pass made on 2026-09-10 while the reference runs computed, to decide what MOECoG copies next.
Sources were read at the level stated (full text, abstract, or a survey's summary); numbers are quoted from the
sources. Roadmap chunks that follow from each point are named at the end.

## 1. Preprocessing: what almost everyone does

| step | consensus | sources |
|---|---|---|
| referencing | common average (or common median) across the good electrodes; Laplacian re-referencing for depth probes | Peterson 2021 (common median), Neuroprobe 2025 (Laplacian), Chang lab (CAR per 16-channel block) |
| line noise | notch at the line frequency and harmonics, Butterworth order 6, about 2.5 Hz wide | speech-decoding pipelines reviewed in Frontiers 2023 |
| drift | high-pass 0.5-5 Hz, or none when the feature is a high-gamma envelope | Frontiers 2023 |
| bad channels | reject electrodes with line noise, poor contact, large shifts, and interictal or epileptiform activity; do it before referencing | Frontiers 2023 |
| the feature | high-gamma amplitude 70-150 Hz (some groups 70-200 Hz): band-pass then Hilbert envelope, or 8 log-spaced bands averaged (Chang lab), then downsampled to 100-200 Hz | Frontiers 2023, Chang lab pipelines in `docs/preprocessing_catalog.md` |
| normalisation | z-score every electrode against a reference period (rest or the session's own mean and variance) | Frontiers 2023, 2024 speech pipelines |
| decoder inputs | 1-200 Hz band-pass, 250 Hz resampling and 2 s windows centred on the event for convolutional decoders | HTNet |

MOECoG already implements CAR (per group), notch, Hilbert envelopes and the Chang-lab 8-band preset as
`raw_steps`, chronological epoching, and a bad-channel union per subject. Missing: an artefact and
epileptiform channel rejection step, per-session z-scoring as a pipeline step, and a Laplacian option for
sEEG. (References: Peterson et al. 2021, J Neural Eng 18:016002, https://doi.org/10.1088/1741-2552/abda0b;
Neuroprobe, https://arxiv.org/abs/2509.21671; "Characterization of high-gamma activity in
electrocorticographic signals", Front Neurosci 2023, https://doi.org/10.3389/fnins.2023.1206120.)

## 2. Transfer across sessions and participants

**Alignment of feature distributions (EEG literature, applies to ECoG within a patient).** Euclidean
Alignment recentres each session's trial covariances to identity (He and Wu 2020); Riemannian Procrustes
Analysis recentres, rescales and rotates covariances on the manifold (Rodrigues et al. 2019); CORAL matches
second-order statistics. A 2026 comparison on 18 subjects (14 EEG channels, CCA decoder) found EA with
regularisation alpha = 100 gave the largest mean gain, +3.44 accuracy points over no alignment (t(17) = 2.48,
p = 0.024), CORAL was the best method for 9 of 18 subjects, and "no single alignment method is universally
optimal"; the authors stress their per-subject best settings are an oracle and need nested cross-validation.
(Front Syst Neurosci 2026, https://doi.org/10.3389/fnsys.2026.1840121; also "Revisiting Euclidean
Alignment", https://arxiv.org/abs/2502.09203.)

**Across participants with different grids (HTNet, Peterson et al. 2021).** The decoder that generalised to
unseen ECoG participants projects each electrode onto 144 sensorimotor regions of the AAL atlas with a
radial-basis kernel (2 cm full width at half maximum), computes spectral power with a Hilbert-transform
layer, and is trained on data pooled from 11 of 12 participants (AJILE12 arm movements, 2 s windows,
1-200 Hz, 250 Hz). Numbers: tailored decoder 84 +- 8 % (EEGNet 73 +- 14 %); unseen participant 72 +- 10 %
(EEGNet 64 +- 8 %); fine-tuning with as few as 50 ECoG or 20 EEG events approached tailored performance;
HTNet was the only decoder that transferred from ECoG-trained to EEG above chance. Baselines were EEGNet, a
random forest and a Riemannian minimum-distance classifier.

**Decoder stability over days (chronic ECoG).** Silversmith et al. 2021 (Nat Biotechnol, 128-channel chronic
ECoG, one paralysed participant) showed that carrying decoder weights across days with continued closed-loop
adaptation consolidates a stable neural map ("plug-and-play"), while daily re-initialisation degrades
performance. Natraj et al. (Cell 2025, bioRxiv 2023) describe a low-dimensional manifold preserved across days
under representational drift, so recalibrating the electrodes-to-manifold map while keeping the
manifold-to-behaviour map fixed maintains control. An iScience 2025 paper reports Riemannian features that keep
movement-trajectory decoding stable across days on ECoG. These match what the benchmark saw on BCI III-1:
band-power features standardised on one session collapse a week later, tangent-space features survive.

**Pretrained representations.** BrainBERT (ICLR 2023) learns masked-spectrogram representations of single
iEEG electrodes; Brant (NeurIPS 2023) is an iEEG foundation model; Population Transformer (ICLR 2025)
pretrains over arbitrary electrode ensembles by adding 3-D electrode coordinates to each electrode's temporal
embedding, and beats Brant on downstream iEEG decoding. Neuroprobe (2025), a 15-task benchmark on Brain
Treebank with within-session, cross-session and cross-subject splits, found a linear decoder on
Laplacian-referenced spectrograms the strongest baseline overall (AUROC 0.660 within, 0.648 cross-session,
0.539 cross-subject) ahead of BrainBERT (0.586 / 0.581) and PopT (0.545 / 0.566). Pretraining helps on some
tasks (sentence onset, speech vs non-speech) and not on most. (https://arxiv.org/abs/2406.03044,
https://arxiv.org/abs/2509.21671.)

**Deep regression of kinematics.** FingerFlex (Lomtev et al. 2022, https://arxiv.org/abs/2211.01960), a
convolutional encoder-decoder on BCI Competition IV dataset 4, reports a correlation up to 0.74 between true
and predicted finger trajectories (the competition winner reached 0.46; the MOECoG ridge baselines sit at
0.28 on the Miller fingerflex files with chronological purge-gapped folds). The gap is the M3 target.

## 3. Evaluation practices worth adopting

- **Chronological splits by default** (Neuroprobe's within-session split trains and tests on different
  segments of the same movie; MOABB's shuffled folds are the exception, not the rule, for non-stationary
  intracranial signals). MOECoG already does this and records the fold policy.
- **Three split types reported side by side**: within-session, cross-session, cross-subject (Neuroprobe,
  MOABB). MOECoG has the first two; cross-subject waits for an electrode aligner.
- **The patient is the unit of statistics**; paired tests across patients, effect sizes, and no pooling of
  folds (MOABB meta-analysis; implemented in `moecog.analysis`).
- **Calibration curves**: report performance against the number of target-patient events used for fine-tuning
  (HTNet: 20, 50, 100 events); this is the learning-curve evaluation MOABB offers as `data_size` policies.
- **Seeds**: deep decoders with three seeds at least; classical pipelines are deterministic under
  chronological folds.
- **Nested cross-validation** for any alignment or model hyper-parameter chosen per subject (the 2026 alignment
  study's oracle warning).
- **A strong linear baseline in every table**: on Neuroprobe it beat the foundation models; on the Miller tier
  band-power LDA beat ShallowFBCSPNet by a wide margin at 48 training trials per patient.

## 4. What MOECoG does with this

| point | chunk | milestone |
|---|---|---|
| per-session z-scoring, Euclidean alignment and Riemannian re-centering as an evaluation option (`alignment=`), applied label-free per session; Riemannian tangent space on the 70-150 Hz band (done: `Riemann HG TS + LogReg`) | `moecog.alignment`, `HilbertEnvelope` before `Covariances` | M2 (Riemann on envelopes), M3 (alignment) |
| artefact and epileptiform channel rejection, Laplacian for depth probes | new `raw_steps` | M3 |
| learning curves with chronological subsets (10/25/50/100 %) | `LearningCurveEvaluation` | M2 |
| electrode-to-region projection (RBF kernel, atlas regions) as the first `aligner` for `CrossSubjectEvaluation`; pooled pretraining then fine-tuning with 20/50/100 events | M4 |
| FingerFlex-style convolutional regressor as a pipeline | M3 |
| BrainBERT and PopT as feature extractors behind a linear head, with the linear spectrogram baseline next to them | M4 |
| Neuroprobe tasks and splits on Brain Treebank as the naturalistic tier | M5 |
| decoder stability across days as a paradigm (BCI III-1 now; AJILE12, ds006890, BRAVO1 later) | M3-M4 |
