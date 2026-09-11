# MOECoG roadmap

*"As long as you have a kid, you are a mother."* MOECoG does not need every dataset and every model to be the
Mother of all ECoG Benchmarks. It needs a package people can install, a contribution path people can follow,
a few reference datasets with regenerable numbers, and a habit of re-evaluating. This file is the plan; it is
rewritten, not appended, whenever the plan changes. History lives in `CHANGELOG.md` and Jira (epic PRSNL-59).

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
6. **Data stay at the source.** MOECoG hosts code, results and summaries; loaders fetch data; nothing under a
   data-use agreement is redistributed.

## Milestones

### M0. A kid: the Miller library end to end (done 2026-09-09)

All 16 experiments load with cue annotations; classification and regression paradigms; within-subject CV with a
decided fold policy; first leaderboard (motor_basic kappa 0.90, faces 0.68, fingerflex ridge r 0.28); the
catalog and smoke sweep of 130 public deposits (106 load).

### M1. A package people can use (target 2026-09-30)

| chunk | definition of done | owner | Jira |
|---|---|---|---|
| Contribution path | `CONTRIBUTING.md`, code of conduct, issue and PR templates, `CITATION.cff`, pre-commit | done 2026-09-10 | PRSNL-78 |
| CI | GitHub Actions runs ruff and the synthetic test suite on Python 3.10-3.12 for every PR; badge in README | done 2026-09-10, first run green on all four jobs | PRSNL-69 |
| YAML pipelines + one-call benchmark | `pipelines/*.yml`, `moecog.pipelines.load_pipelines`, `moecog.benchmark(...)` reproduces `results/*.csv` | done 2026-09-10 | PRSNL-79 |
| 0.2.0 on PyPI | `pip install moecog` works in a clean environment; release notes from CHANGELOG; GitHub release tagged `v0.2.0` | done 2026-09-10 (https://pypi.org/project/moecog/0.2.0/, fresh-venv install verified) | PRSNL-69 |
| Docs site | MkDocs (material) built by Actions to GitHub Pages: install, quickstart, datasets table, smoke table, leaderboard, atlas, API | site and workflow committed 2026-09-10; Pages setting needs Yifan | PRSNL-80 |
| MOABB parity batch 1 | `docs/moabb_review.md` decisions implemented: results store with digests, cross-session evaluation, meta-analysis and plots, pipelines and contexts inside the wheel, config helpers, changelog/link/download workflows, examples | done 2026-09-10 | PRSNL-81 |
| Zenodo DOI | GitHub release archived on Zenodo; DOI in README and CITATION | after 0.2.0 | PRSNL-80 |

### M2. Reference benchmark on the Miller tier (target 2026-10-31)

| chunk | definition of done |
|---|---|
| Reference tasks | five tasks fixed and documented: motor_basic hand vs tongue, faces_basic, gestures, imagery_basic, fingerflex regression |
| Pipeline set | the five YAML baselines plus a Riemannian pipeline (pyriemann) and one braindecode model (ShallowFBCSPNet) on CPU; done 2026-09-10 (PRSNL-82) |
| Numbers | `results/reference_<task>.csv` for every task x pipeline, 5 chronological folds, three seeds where randomness enters; leaderboard regenerated (`scripts/run_reference.py`, PRSNL-83, running) |
| Analysis | per-patient distributions and a paired comparison (MOABB-style meta-analysis) in `docs/analysis.md` (`scripts/build_analysis.py`, PRSNL-83) |
| Second evaluation | `CrossSessionEvaluation` exists (M1 batch); on the Miller tier most "sessions" are task variants rather than repeat days, so it is run only where a task repeats (speech_lists L1 vs L2) and reported with that caveat |

### M3. Second dataset family and the regression story (target 2026-11-30)

| chunk | definition of done |
|---|---|
| BCI Competition IV-4 and III-1 | numbers reproduce the published competition scores within tolerance |
| Merk grip force + Peterson pose | regression paradigms for force and 2-D pose; ridge and PACE baselines |
| Detroit naming corpora (ds006910, ds006234, ds005545) | 100+ patient classification with the epoched paradigm; per-patient distribution plotted |
| Stimulus reconstruction | `SpectrogramReconstruction` paradigm on Bellier and Verwoert |

### M4. Cross-subject and transfer (target 2027-01)

Cross-subject evaluation with electrode-count alignment, the PACE isoparametric decoders as pipelines, a transfer
table that reproduces the PACE camera-ready null result on the benchmark.

### M5. Speech tier and community (2027 H1)

Bouchard CV syllables, Verwoert, Du-IN, tonal speech; a speech paradigm with word error metrics; first external
contributor; a benchmark paper draft.

### Parked

Registration-gated sources (PRSNL-77), MEF3 on DANDI, pymef edge cases, spikes-only sets, non-human tier, lazy
loading of hour-long runs, CodeCarbon, optuna. They come back when a milestone needs them.

## What needs Yifan

- Enabling GitHub Pages on the repository for the docs site.
- Tier and licence policy (PRSNL-75), outreach sends (PRSNL-73), registrations (PRSNL-77).

## Re-evaluation log

- 2026-09-10 (later): "copy everything MOABB did, better": `docs/moabb_review.md` is the component-by-component decision list; batch 1 of it shipped the same day (analysis, cross-session, store, docs site); cross-subject with an explicit aligner stays in M4, learning curves in M2.
- 2026-09-10: pivot from "test everything" to "package + contribution path + chunks". The catalog sweep stays as
  the map. Dropped from the near term: the remaining blocked sources, the non-human tier, lazy loading.
