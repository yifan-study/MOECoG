# First classification-tier baselines (2026-09-09)

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
(PRSNL-67): chronological folds need a class-balance check or a fallback to
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
