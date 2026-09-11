# Reference protocol (roadmap M2, 2026-09-10)

The reference benchmark on the Miller tier is produced by `scripts/run_reference.py` into
`results/reference_<task>.csv` (a `ResultsStore`: one row per patient, session, pipeline, metric and fold,
with parameter digests and the package version), summarised by `scripts/build_leaderboard.py`
(`docs/leaderboard.md`) and analysed by `scripts/build_analysis.py` (`docs/analysis.md`, `docs/figures/`).

**Tasks.** `motor_basic` hand vs tongue (19 patients), `faces_basic` face vs house (14), `imagery_basic` overt
and imagined hand vs tongue (7, two sessions), `gestures` (5, several sessions), `fingerflex` dataglove
regression (9), and BCI Competition III dataset I (1 patient, two sessions a week apart, the competition's
published test labels attached).

**Paradigms.** Band-pass 1-200 Hz, ECoG channels only, epochs from cue onset to cue end (or 1 s windows
where the preset says so); `FingerFlexionRegression` uses causal 0.5 s windows with a 50 ms stride.
Deep pipelines see the same epochs resampled to 250 Hz.

**Evaluations.** `WithinSubjectCV` with 5 chronological contiguous folds per (patient, session), stratified
shuffled folds only where a file presents its cues in blocks (`fold_policy` column); regression folds carry
a purge gap. `CrossSessionEvaluation` (leave one session out) on BCI III-1. `LearningCurveEvaluation` on the
Miller classification tasks: the last 20 % of each (patient, session) in recording order is the test block
for every point; training uses the first 10, 25, 50 or 100 % of the remaining trials, so a small budget means
the earliest minutes of the session, as a calibration phase would.

**Pipelines.** The reference YAMLs shipped in the package: `LogBandPower + LDA`, `LogBandPower + LogReg`,
`HighGamma + LDA`, `Riemann TS + LogReg` (covariances on the raw epochs), `Riemann HG TS + LogReg` (covariances of
the 70-150 Hz band-passed epochs), `Riemann Env TS + LogReg` (pyriemann `ERPCovariances` with class prototypes of the
log high-gamma envelope, eight SVD components per class), `ShallowFBCSPNet` (braindecode,
150 epochs of batch 16, AdamW 6.25e-4, per-channel standardisation on the training fold, CPU); regression
uses `LogBandPower + Ridge` and `HighGamma + Ridge`. Randomness enters only through the deep model, which is
run with seeds 0, 1, 2 (`ShallowFBCSPNet s<k>` rows).

**Metrics.** Kappa is the headline for trials, Pearson r for kinematics; accuracy, balanced accuracy and r2 are
recorded alongside. Statistics across patients use paired tests (permutation below 20 patients), effect sizes
d_z and Stouffer combination, see `docs/moabb_review.md` section 7.

**Where it ran.** Classical pipelines on a laptop CPU (Python 3.12, NumPy 2, mne 1.13, scikit-learn 1.7,
pyriemann 0.12); the deep pipeline in a NumPy 1 environment on the same machine because the last torch build
for Intel macOS predates NumPy 2. Athene (CPU) reruns the seeds when it is reachable; no GPU is used before
the PACE camera-ready (2026-09-25).

## Findings so far (2026-09-11, seed 0 of the deep model)

- **Band power with a linear classifier is the reference to beat on small per-patient sets.** With 60 cued trials per
  patient (motor_basic, imagery_basic) `LogBandPower + LDA` and `HighGamma + LDA` lead every pairwise test;
  `ShallowFBCSPNet` at 150 epochs reaches kappa 0.44 on motor_basic and 0.21 on imagery against 0.92 and 0.66
  (d_z above 1.1 in every comparison, permutation p < 0.001 on motor).
- **The deep model wins where trials are many and the signal is evoked.** faces_basic (300 trials of 400 ms per
  patient): ShallowFBCSPNet 0.76 against 0.68 for the best band-power pipeline, ahead of every classical pipeline
  (p between 0.0005 and 0.034, d_z 0.47 to 0.90, Friedman p = 0.003); its median patient reaches 0.84.
- **Gestures is the hard task**: five patients, several sessions of a few trials, best kappa 0.52 (HighGamma + LDA),
  the network near chance (0.04).
- **Riemannian tangent space on raw-epoch covariances trails band power within a session** on every Miller task,
  but is the only pipeline that survives the week between the BCI III-1 sessions (kappa 0.52 versus 0.00 to 0.36):
  standardising band power on one session does not transfer, covariance geometry partly does. Tangent space on
  high-gamma envelopes and per-session alignment are the next chunks (roadmap M2/M3).
- **Fingerflex**: HighGamma + Ridge r 0.28 beats LogBandPower + Ridge 0.27 in 9 of 9 patients (p = 0.016); both sit
  far below the 0.74 that FingerFlex's convolutional decoder reports, the M3 target.

Seeds 1 and 2 of the deep model are pending; the numbers above will move by a few hundredths, not in rank.

---

# First classification-tier baselines (2026-09-09, superseded by the reference protocol above)

Run on FAU Athene (`debug` partition, CPU only, job 4721651) against the
library copy at `/mnt/archive/home/yyu2024/PLaCT_data` with
`scripts/run_baseline.py` at commit `1df618b`. These are sanity numbers for the
pipeline, not benchmark results: one seed, classical features, no channel
rejection, no hyper-parameter search.

**Protocol.** Band-pass 1-200 Hz, ECoG channels only, epochs from cue onset to
cue end (3 s motor, 0.4 s faces), `WithinSubjectCV` with 5 chronological
contiguous trial folds per (patient, session), scored with accuracy, balanced
accuracy and Cohen's kappa. Pipelines: `HighGamma+LDA` (log 70-150 Hz Welch
power per channel, standardised, shrinkage LDA) and `LogBandPower+LDA` (mu,
beta, low gamma, high gamma per channel).

## motor_basic: hand (fist) vs tongue, 19 patients, 30 + 30 trials each

| Pipeline | Accuracy | Balanced acc. | Kappa | Kappa, undefined folds as 0 |
|---|---|---|---|---|
| HighGamma+LDA | 0.937 | 0.943 | 0.860 | 0.823 |
| LogBandPower+LDA | 0.956 | 0.958 | 0.899 | 0.861 |

Per patient (accuracy, HighGamma+LDA / LogBandPower+LDA): bp 0.98/0.98, ca
0.87/0.93, cc 1.00/1.00, de 0.95/1.00, fp 0.97/0.93, gc 1.00/1.00, gf
0.92/0.87, hh 0.83/0.93, hl 0.80/0.88, jc 1.00/1.00, jf 1.00/1.00, jm
0.92/0.87, jp 0.68/1.00, jt 0.92/0.90, rh 0.97/0.95, rr 1.00/0.92, ug
1.00/1.00, wc 1.00/1.00, zt 1.00/1.00.

Patient jf presented its cues in blocks rather than interleaved, so 8 of its
10 chronological test folds contain a single class (kappa undefined,
accuracy still valid). This is the concrete case for the fold-policy decision
(BCI-27): chronological folds need a class-balance check or a fallback to
stratified folds for block-ordered files.

## faces_basic: face vs house pictures (400 ms), 14 patients, 150 + 150 trials

| Pipeline | Accuracy | Balanced acc. | Kappa |
|---|---|---|---|
| HighGamma+LDA | 0.818 | 0.820 | 0.638 |
| LogBandPower+LDA | 0.841 | 0.841 | 0.682 |

Per patient (accuracy, LogBandPower+LDA): aa 0.64, ap 0.73, ca 0.89, de 0.91,
fp 0.99, ha 0.94, ja 0.91, jm 0.68, jt 0.85, mv 0.96, rn 0.79, rr 0.60, wc
0.91, zt 0.98. The two weakest (aa, rr) are the patient with the anomalous
amplitude range and the one with only 100 + 100 trials and 40 channels; Miller
(2016) decoded these data from the ERP plus broadband, which the 400 ms
band-power window here ignores in part.

## imagery_basic: hand vs tongue, 7 patients, overt (`mot`) and imagery (`im`) sessions

| Session | Pipeline | Accuracy | Balanced acc. | Kappa |
|---|---|---|---|---|
| mot (overt) | HighGamma+LDA | 0.948 | 0.954 | 0.893 |
| im (imagery) | HighGamma+LDA | 0.710 | 0.714 | 0.417 |

Per patient (accuracy, overt / imagery): bp 0.98/0.57, fp 0.95/0.70, hh
0.83/0.70, jc 1.00/0.90, jm 0.92/0.75, rh 0.95/0.68, rr 1.00/0.67. Imagery
sits well above chance for six of seven patients and near chance for bp,
consistent with Miller (2010) and with the notes that some patients found the
imagery task difficult.

## What these numbers say about the pipeline

- The loaders, annotations, epoching and CV produce sensible, patient-level
  numbers on three experiments with no manual fixes.
- Classical band power already separates overt movement almost perfectly;
  the room for deep models is in imagery, visual categorisation with short
  windows, and the harder experiments (n-back, visual search, speech).
- Wall-clock on 8 CPU cores: 141 s for motor_basic (19 patients x 2
  pipelines), 88 s for faces_basic, 51 s for imagery_basic.

## Rerun 2026-09-09 (fold policy active, finger flexion added; job 4721667, 19 min 50 s)

`WithinSubjectCV` now checks every chronological fold and switches block-ordered
files to stratified shuffled folds (`fold_policy` column). Two motor_basic
patients fell back (gf, jf), so kappa is defined for every patient:
LogBandPower+LDA kappa 0.917 (was 0.899 with two undefined patients),
HighGamma+LDA 0.877. faces_basic and imagery_basic are unchanged (no
block-ordered files).

First continuous-tier baseline, fingerflex (9 patients, 500 ms windows, 50 ms
stride, causal target, 5 chronological folds with a purge gap):

| Pipeline | Pearson r (mean over fingers and patients) | R2 |
|---|---|---|
| HighGamma+Ridge | 0.283 | -0.14 |
| LogBandPower+Ridge | 0.265 | -0.21 |

Per patient (r, HighGamma+Ridge): bp 0.30, cc 0.45, ht 0.20, jc 0.33, jp 0.29,
mv 0.26, wc 0.20, wm 0.22, zt 0.31. This is the classical band-power reference
the roadmap predicted (0.3-0.5); the deep decoders of TRACE and PACE reach
0.5-0.74 on the same patients under their own protocol, so the gap is the
benchmark's room. The negative R2 comes from unnormalised ridge predictions on
raw dataglove units; the leaderboard reports r.
