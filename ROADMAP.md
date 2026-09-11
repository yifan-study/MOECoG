# MOECoG roadmap

*"As long as you have a kid, you are a mother."* MOECoG does not need every dataset and every model to be the
Mother of all ECoG Benchmarks. It needs a package people can install, a contribution path people can follow,
a few reference datasets with regenerable numbers, and a habit of re-evaluating. This file is the plan; it is
rewritten, not appended, whenever the plan changes. History lives in `CHANGELOG.md` and Jira project BCI
(epic BCI-2; the tickets moved out of PRSNL on 2026-09-10, old PRSNL keys still resolve).

Status 2026-09-10: M0 done, M1 in progress. The 130-entry catalog with 106 loading is a map of the territory,
not a to-do list; the milestones below pick what to walk first.

## Principles

1. **Ship the package before the paper.** Releases on PyPI with CI green; the docs describe what the release does.
2. **One chunk is one PR is one week or less.** If a chunk cannot be finished and merged in a week, split it.
3. **Every chunk has a definition of done** written before the work starts, and a number or a table at the end.
4. **Re-evaluate monthly.** On the first working day of each month: read the smoke table, the leaderboard and
   this file; drop or defer anything that no longer earns its place; write the decision in Jira and here.
5. **Follow MOABB where it worked, deviate where ECoG differs** (`docs/moabb_lessons.md`): per-patient evaluation,
   regression as a first-class citizen, a catalog with statuses.
6. **Read before building.** Every milestone starts from `docs/best_practices.md` (what the field does for preprocessing, transfer and evaluation) and `docs/moabb_review.md`; a technique enters the roadmap only with the paper that motivates it.
7. **Data stay at the source.** MOECoG hosts code, results and summaries; loaders fetch data; nothing under a
   data-use agreement is redistributed.

## Milestones

### M0. A kid: the Miller library end to end (done 2026-09-09)

All 16 experiments load with cue annotations; classification and regression paradigms; within-subject CV with a
decided fold policy; first leaderboard (motor_basic kappa 0.90, faces 0.68, fingerflex ridge r 0.28); the
catalog and smoke sweep of 130 public deposits (106 load).

### M1. A package people can use (target 2026-09-30)

| chunk | definition of done | owner | Jira |
|---|---|---|---|
| Contribution path | `CONTRIBUTING.md`, code of conduct, issue and PR templates, `CITATION.cff`, pre-commit | done 2026-09-10 | BCI-37 |
| CI | GitHub Actions runs ruff and the synthetic test suite on Python 3.10-3.12 for every PR; badge in README | done 2026-09-10, first run green on all four jobs | BCI-23 |
| YAML pipelines + one-call benchmark | `pipelines/*.yml`, `moecog.pipelines.load_pipelines`, `moecog.benchmark(...)` reproduces `results/*.csv` | done 2026-09-10 | BCI-32 |
| 0.2.0 on PyPI | `pip install moecog` works in a clean environment; release notes from CHANGELOG; GitHub release tagged `v0.2.0` | done 2026-09-10 (https://pypi.org/project/moecog/0.2.0/, fresh-venv install verified) | BCI-23 |
| Docs site | MkDocs (material) built by Actions to GitHub Pages: install, quickstart, datasets table, smoke table, leaderboard, atlas, API | site and workflow committed 2026-09-10; Pages setting needs Yifan | BCI-33 |
| MOABB parity batch 1 | `docs/moabb_review.md` decisions implemented: results store with digests, cross-session evaluation, meta-analysis and plots, pipelines and contexts inside the wheel, config helpers, changelog/link/download workflows, examples | done 2026-09-10 | BCI-30 |
| Zenodo DOI | GitHub release archived on Zenodo; DOI in README and CITATION | after 0.2.0 | BCI-33 |

### M2. Reference benchmark on the Miller tier (target 2026-10-31)

| chunk | definition of done | status |
|---|---|---|
| Reference tasks | six tasks fixed and documented in `docs/baselines.md`: motor_basic hand vs tongue, faces_basic, gestures, imagery_basic, fingerflex regression, BCI III-1 (two sessions) | done 2026-09-10 |
| Pipeline set | the five YAML baselines plus a Riemannian pipeline (pyriemann) and one braindecode model (ShallowFBCSPNet) on CPU; done 2026-09-10 (BCI-31) |
| Numbers | `results/reference_<task>.csv` for every task x pipeline, 5 chronological folds, three seeds where randomness enters; leaderboard regenerated | classical set done 2026-09-10 (motor 0.92, faces 0.68, imagery 0.66, gestures 0.49, fingerflex r 0.28, BCI III-1 within 0.82 / cross-session 0.52); ShallowFBCSPNet seed 0 running, seeds 1-2 on Athene (BCI-34) |
| Analysis | per-patient distributions and a paired comparison (MOABB-style meta-analysis) in `docs/analysis.md` (`scripts/build_analysis.py`) | done 2026-09-10, regenerated after every run |
| Second evaluation | `CrossSessionEvaluation` on BCI III-1 (train and test sessions a week apart, published labels attached): kappa 0.75-0.86 within a session, 0.00-0.52 across; Riemannian tangent space transfers best | done 2026-09-10; Miller "sessions" are task variants, so no cross-session there |
| Learning curves | `LearningCurveEvaluation` (train on 10/25/50/100 % of a patient's trials, chronological), the MOABB `data_size` policies; HTNet reports tailored performance from about 50 events | to do (last M2 chunk) |
| Better Riemannian baseline | tangent space on high-gamma envelope covariances (`HilbertEnvelope` raw step before `Covariances`) instead of raw-epoch covariances, which trail band power within session | to do (M2) |

### M3. Second dataset family and the regression story (target 2026-11-30)

| chunk | definition of done |
|---|---|
| BCI Competition IV-4 and III-1 | numbers reproduce the published competition scores within tolerance |
| Merk grip force + Peterson pose | regression paradigms for force and 2-D pose; ridge and PACE baselines |
| Detroit naming corpora (ds006910, ds006234, ds005545) | 100+ patient classification with the epoched paradigm; per-patient distribution plotted |
| Stimulus reconstruction | `SpectrogramReconstruction` paradigm on Bellier and Verwoert |
| Session drift | per-session feature normalisation and Euclidean / Riemannian Procrustes alignment as pipeline steps (`moecog.pipelines.alignment`), evaluated on BCI III-1 cross-session and on the Miller multi-session files; the literature says alignment is worth 3-10 points and no single method wins (`docs/best_practices.md`) |
| Deep fingerflex | a FingerFlex-style convolutional regressor as a pipeline, to test the published r above 0.6 on BCI IV-4 against ridge's 0.28 |

### M4. Cross-subject and transfer (target 2027-01)

| chunk | definition of done |
|---|---|
| Electrode aligner | `CrossSubjectEvaluation(aligner=...)` with the HTNet recipe as the first aligner: radial-basis projection of electrodes onto atlas regions (2 cm kernel, sensorimotor AAL regions) from `ElectrodeInfo` MNI coordinates, so patients with different grids share a feature space; refuses to run without an aligner |
| Fine-tuning protocol | pooled-patient pretraining then fine-tuning with 20 / 50 / 100 target events (HTNet's budget), reported as a calibration curve next to the tailored decoder |
| PACE decoders | the PACE isoparametric decoders as pipelines; the transfer table reproduces the PACE camera-ready null result on the benchmark |
| Foundation-model pipelines | BrainBERT and Population Transformer as feature extractors behind a linear head (electrode coordinates as inputs), compared with the linear spectrogram baseline that beats them on Neuroprobe |

### M5. Speech tier and community (2027 H1)

Bouchard CV syllables, Verwoert, Du-IN, tonal speech; a speech paradigm with word error metrics; the Neuroprobe
tasks on Brain Treebank as a naturalistic tier (their splits: within-session, cross-session, cross-subject); first
external contributor; a benchmark paper draft.

### Parked

Registration-gated sources (BCI-36), MEF3 on DANDI, pymef edge cases, spikes-only sets, non-human tier, lazy
loading of hour-long runs, CodeCarbon, optuna. They come back when a milestone needs them.

## What needs Yifan

- Enabling GitHub Pages on the repository for the docs site.
- Jira: a PhD project with its own boards (MOECoG board = filter on this epic); creating projects and boards needs the UI, the proposal is on the decision ticket.
- Tier and licence policy (BCI-38), outreach sends (BCI-25), registrations (BCI-36).

## Re-evaluation log

- 2026-09-10 (night): M2 classical set done in one day; the surprise is BCI III-1's cross-session drop, so session drift moves up: alignment steps into M3, the HTNet electrode aligner and fine-tuning budgets define M4, foundation models become pipelines rather than a separate tier. Learning curves stay the last M2 chunk. Literature pass recorded in `docs/best_practices.md`.
- 2026-09-10 (later): "copy everything MOABB did, better": `docs/moabb_review.md` is the component-by-component decision list; batch 1 of it shipped the same day (analysis, cross-session, store, docs site); cross-subject with an explicit aligner stays in M4, learning curves in M2.
- 2026-09-10: pivot from "test everything" to "package + contribution path + chunks". The catalog sweep stays as
  the map. Dropped from the near term: the remaining blocked sources, the non-human tier, lazy loading.
