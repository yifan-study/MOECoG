# Preprocessing pipelines across ECoG and iEEG decoding, and what MOECoG offers

A benchmark that wants to reproduce "the number in the paper" has to reproduce
the paper's signal chain. This page collects the chains used by the groups
whose datasets are in `docs/dataset_catalog.md`, then maps each to a MOECoG
preset. Numbers marked verify come from memory of the papers and must be
checked before we cite them.

## 1. Referencing

| Scheme | Used by | MOECoG |
|---|---|---|
| Common average reference over all good channels | Miller library scripts (`car.m`), Podcast, Visual ECoG, Peterson/HTNet, Duraivel µECoG, most grid work | `CommonAverageReference()` |
| CAR per amplifier block (16 or 32 channels) | Chang lab (Bouchard 2013 and later) | `CommonAverageReference(groups=...)` |
| Bipolar between neighbouring contacts | sEEG standard (RAM often uses bipolar pairs; Cogitate; Brain Treebank Laplacian variant) | planned `BipolarReference()` |
| Laplacian (neighbourhood average) | BrainBERT / Brain Treebank | planned |
| White-matter or scalp reference kept as recorded | Miller (scalp reference), Merk (recorded reference) | default (no re-reference) |
| Adjusted CAR for stimulation artefacts (CARLA) | Hermes/Utrecht CCEP sets | out of scope for now |

## 2. Line noise and band limits

- Notch at 60 Hz and harmonics (US data), 50 Hz (EU, Asia). Chang, Podcast,
  Bellier, Merk all notch; Miller's amplifiers have a 1-pole 0.15-200 Hz
  analogue band-pass and the library keeps line noise. MOECoG: `NotchFilter`.
- Paradigm band-pass: MOECoG epoched paradigms default to 1-200 Hz; regression
  paradigms 1-200 Hz before windowing (PACE used 40-300 Hz wavelets on raw).

## 3. Feature representations

| Representation | Definition | Used by | MOECoG |
|---|---|---|---|
| High-gamma analytic amplitude, single band | band-pass 70-150 Hz (or 70-170, 70-200), Hilbert envelope, log or z-score, decimate to 100-500 Hz | Verwoert 70-170 Hz 50 ms windows; Bellier HFA 70-150 at 100 Hz; Podcast 70-200 Hz; Duraivel 70-150 Hz; Natraj; Cogitate HGA | `HilbertEnvelope(bands={"hg": (70, 150)})` |
| High-gamma, 8 log-spaced sub-bands averaged | 8 bands between 70 and 150 Hz, Hilbert each, average, z-score, 200-400 Hz | Chang lab (Bouchard 2013, Moses 2021, Metzger 2023) | `chang_high_gamma()` preset |
| Broadband via PCA decoupling | log-spectra, PCA, project out the first component, exponentiate | Miller 2009 "broadband" (fhpred_master.m) | planned `BroadbandPCA` |
| Wavelet spectrogram (Lomtev) | 40 log-spaced Morlet wavelets 40-300 Hz, downsample 1 kHz to 100 Hz, robust scaling, 200 ms lag | FingerFlex 2022, DTCNet, TRACE, PACE | in PACE repo (`preprocessing_lomtev.py`); port planned |
| Log band power (Welch) | mu 8-13, beta 13-30, low gamma 30-70, high gamma 70-150 | MOECoG baselines; Schalk 2007 / Kubanek 2009 used LMP + 8-12 / 18-24 / 35-42 / 42-70 / 70-100 / 100-140 / 140-170 Hz (verify bands) | `LogBandPower`, `HighGammaPower` |
| Local motor potential (LMP) | low-pass or moving average of the raw signal, ~0-5 Hz | Schalk 2007 cursor, Kubanek 2009 finger, PACE cursor `lmp_only` | planned `LocalMotorPotential` |
| Morlet log-power, 8 bands 3-180 Hz | log power per band, z-score per session | Kahana lab (RAM classifiers) | `LogBandPower(bands=RAM_BANDS)` (config) |
| py_neuromodulation features | 100 ms windows: band power 6 bands, Hjorth, sharp-wave, bursts; 10 s normalisation | Merk 2022 | reuse py_neuromodulation as a pipeline step (optional dependency) |
| STFT / superlet spectrogram at 2048 Hz | 1 s windows | BrainBERT, Neuroprobe baselines | planned |
| Raw voltage, downsampled | 500 Hz, learned filters | HTNet (AJILE12), Peterson move vs rest | no feature step (deep decoders) |
| Discrete tokens (VQ) of 1-200 Hz signal | Du-IN | Du-IN | out of scope |

## 4. Windows, lags and targets

- Continuous kinematics: 500 ms windows, 50 ms stride, target at window end
  (MOECoG causal default), 200 ms neural-to-behaviour lag in Lomtev/PACE;
  cursor velocity rather than position (PACE, `CursorRegression`).
- Cued trials: cue onset to cue end (3 s motor, 0.4 s faces, 1.6 s speech cues);
  Cogitate 0.5-1.5 s stimulus windows; RAM encoding windows of 1.6 s from word
  onset (verify); Neuroprobe 1 s windows.
- Speech synthesis: 50 ms frames of high gamma with 200 ms context stacked
  (Verwoert); Chang: 200 Hz frames into RNN/CTC.

## 5. Artefact and channel handling

- Clinician-marked epileptic or noisy channels removed (Miller motor/imagery;
  Chang; Cogitate); Miller library keeps unrejected channels elsewhere.
- Variance or line-noise based automatic rejection (Podcast, Peterson).
- Acoustic contamination checks for speech production (Roussel 2020; Flinker
  repo): correlate audio and neural spectrograms, drop contaminated channels.
- MOECoG: `DropChannels(z_thresh=...)` planned; datasets may carry a
  `bad_channels` list.

## 6. Splits and metrics used by the source groups

| Setting | Source groups | MOECoG |
|---|---|---|
| Fixed competition split | BCI-IV (400 k train / 200 k test), BCI-III (two sessions) | `CompetitionSplitEval` planned |
| Contiguous temporal train/val/test | FingerFlex, TRACE, PACE (70/15/15 or fullsplit) | regression folds are contiguous; purge gap |
| Stratified shuffled trial CV | MOABB, most classification papers | `shuffle=True` or automatic fallback |
| Leave-one-session-out | BCI-III, Natraj multi-day, RAM sessions | `CrossSessionEval` (BCI-29) |
| Leave-one-subject-out with alignment | HTNet, Neuroprobe cross-subject, DIVER-1 | `CrossSubjectTransfer` (BCI-29) |
| Metrics | r (kinematics), accuracy/kappa/AUC (trials), WER/PER/CER (speech), spectrogram r (synthesis), encoding r (podcast) | kappa headline for trials, r for kinematics; speech metrics planned |

## 7. What MOECoG implements today

`moecog.preprocessing`:

- `CommonAverageReference(groups=None)`: Raw-level step, optionally per group
  of channels.
- `NotchFilter(freqs=(60, 120, 180))`.
- `HilbertEnvelope(bands, sfreq, log=True, decimate=None)`: epoch-level
  transformer returning amplitude envelopes (n, ch x bands, t) or their
  time-average when `average=True`.
- `chang_high_gamma()`: eight log-spaced bands 70-150 Hz averaged, z-scored.
- Every paradigm accepts `raw_steps=[...]` so a Raw-level chain (CAR, notch)
  runs before epoching or windowing; feature transformers go into the sklearn
  pipeline.

Missing and planned: bipolar/Laplacian references, broadband PCA, LMP, the
Lomtev wavelet port, py_neuromodulation adapter, STFT features.
