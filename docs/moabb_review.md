# MOABB, component by component, and what MOECoG changes

Read on 2026-09-10 from the MOABB source (`yifan-study/moabb`, upstream `NeuroTechX/moabb`, 28k lines of
package code, 84 contributors, releases to v1.7.1) and from its open issues. Each section says what MOABB built,
what its users complain about, and what MOECoG does with it: **copy**, **adapt**, or **improve**. Status
columns refer to `ROADMAP.md` milestones.

## 1. Datasets

**MOABB.** `BaseDataset(subjects, sessions_per_subject, events, code, interval, paradigm, doi)` with
`get_data(subjects) -> {subject: {session: {run: Raw}}}`, `data_path`, `download`, a metaclass that validates
CamelCase codes and session/run naming, a per-subject BIDS cache (`CacheConfig`: save raw / epochs / arrays,
use, overwrite), `BaseBIDSDataset` and `LocalBIDSDataset` for BIDS deposits without writing a class,
`CompoundDataset` to assemble subjects from several datasets, `FakeDataset` for tests, and summary CSV tables
per paradigm that feed an auto-generated docs page. Downloads go through pooch into `~/mne_data`
(`set_download_dir`).

**Complaints (issues).** Datasets loaded as generic EEG1..EEGn without montage; inconsistent class parameters;
BIDS subject labels assumed numeric; requests for lazy loading and static (metadata-only) analysis; dataset
defects only discovered by a full-catalogue sweep; a 2025 issue titled "Ecog data" with no answer.

**MOECoG.**
- Copy the contract (`get_data` nesting, `code`, `interval`, `sfreq`, `doi`), `FakeECoGDataset`,
  `BIDSiEEGDataset(root=...)` as the `LocalBIDSDataset` equivalent. Done.
- Improve: subjects are strings (BIDS labels as they are), channel types carry the electrode kind (`ecog` for
  data, `misc` for everything else) and `ElectrodeInfo` carries coordinates, so the montage problem MOABB
  hit does not recur. Done.
- Improve: the catalog is a registry with statuses (`ok`, `unsupported`, `blocked` with a reason) and a scheduled
  smoke sweep, which is the "full-catalogue sweep" MOABB does by hand. Done; make it a scheduled CI job (M1).
- Improve: `max_runs` / `max_seconds` memory guards on loaders; lazy `preload=False` reading is on the roadmap
  (M3), which is MOABB's open "lazier data loading" request.
- Skip for now: `CompoundDataset` and the BIDS preprocessing cache. ECoG datasets are per-patient; pooling is
  a paradigm decision, not a dataset one.

## 2. Paradigms

**MOABB.** `BaseProcessing` builds scikit-learn "process pipelines" (raw -> events -> epochs -> arrays) with
filter banks, `tmin`/`tmax` relative to the dataset interval, `baseline`, `channels`, `resample`, and
`overlap` for pseudo-online windows; paradigms are per-BCI-family (`MotorImagery`, `P300`, `SSVEP`, `CVEP`,
`FixedIntervalWindowsProcessing`, `RestingStateToP300Adapter`); `scoring()` picks accuracy or ROC-AUC.

**Complaints.** "Make the paradigms more broadly"; the filter-bank paradigm does not fit the newer
abstraction; label handling through MNE options is awkward; preprocessing documentation unclear.

**MOECoG.**
- Copy `tmin`/`tmax`/`fmin`/`fmax`/`resample`/`channels` and the "paradigm decides the metric" rule. Done.
- Improve: two base kinds from the start, `BaseClassificationParadigm` (epochs from annotations) and
  `BaseRegressionParadigm` (causal windows with a continuous target from `misc` channels). MOABB has no
  regression paradigm; ECoG decoding is half regression. Done.
- Improve: `raw_steps` (CAR, notch, Hilbert envelopes, Chang-lab high gamma) are explicit objects passed to the
  paradigm, documented in `docs/preprocessing_catalog.md`, instead of implicit MNE options. Done.
- Adapt: filter banks become a `raw_step`, not a paradigm family (M2).
- Improve: the headline metric is kappa (chance-corrected) for classification and Pearson r for regression, so
  2-class and 15-class results sit in one table. Done.

## 3. Evaluations and splitters

**MOABB.** `WithinSessionEvaluation` (stratified shuffled K-fold inside each session), `CrossSessionEvaluation`
(leave-one-session-out), `CrossSubjectEvaluation` (leave-one-subject-out, sessions concatenated), a newer
`splitters` module (`WithinSessionSplitter`, `CrossSessionSplitter`, `CrossSubjectSplitter`,
`LearningCurveSplitter` with `data_size` policies), grid search inside the evaluation, optuna, model saving,
CodeCarbon emissions, `is_valid` with a reason message.

**Complaints.** Splitters silently overriding explicit `n_splits`; a metadata-aware splitter cannot be passed
directly; grid search should live in the pipeline, not the evaluation; results should be pushed as soon as
they are computed; cross-subject should support transfer learning; a "critical difference" visualisation is
missing.

**MOECoG.**
- Improve: chronological contiguous folds are the default for classification (ECoG is non-stationary within a
  session) with a stratified-shuffled fallback for block-ordered cues, and the fold policy is a result column.
  Regression folds carry a purge gap. Done (BCI-27).
- Copy: `CrossSessionEvaluation` (leave-one-session-out per patient, sessions in chronological order) and
  `is_valid` with reasons. This batch.
- Improve: `CrossSubjectEvaluation` cannot concatenate patients with different grids. It takes an explicit
  `aligner` (a fitted transform to a shared space: anatomical ROI pooling from `ElectrodeInfo`, channel-count
  padding, or a learned alignment) and refuses to run without one. M4, with the PACE transfer decoders.
- Copy: learning curves (`data_size` policies) because ECoG has few trials per patient. M2.
- Improve: grid search is a pipeline step (`GridSearchCV` inside the estimator), never an evaluation option.
  Documented in `CONTRIBUTING.md`.
- Improve: results are appended per (dataset, subject, session, pipeline) as they finish (MOABB's open request),
  with a digest so reruns skip what exists. This batch.
- Skip: CodeCarbon, optuna, model saving until a milestone needs them.

## 4. Results storage and bookkeeping

**MOABB.** `Results`: one HDF5 file keyed by pipeline digest (hash of the pipeline repr) and dataset, rows of
(score, time, samples), `not_yet_computed` to skip finished (pipeline, dataset, subject) triples, `overwrite`
and `suffix` options, `to_dataframe`. The benchmark paper's tables are committed as CSV/JSON in `results/`.

**Complaints.** Digest keyed on `repr`, so a cosmetic change reruns everything; HDF5 locking on shared
filesystems; results only written at the end of a dataset.

**MOECoG.**
- Adapt: `moecog.analysis.ResultsStore`, one tidy CSV per store (git-friendly, no HDF5 locks), rows keyed by a
  digest of the pipeline's `get_params()` (not its repr), the paradigm's parameters and the package version;
  `not_yet_computed`, `overwrite`, incremental append. This batch.
- Copy: committed result tables in `results/` regenerated by scripts, rendered in `docs/leaderboard.md`. Done.

## 5. Pipelines

**MOABB.** Pipelines as YAML in a top-level `pipelines/` folder (name, paradigms, citations, steps, optional
`param_grid`), parsed by `parse_pipelines_from_directory`; feature transformers (`LogVariance`, `FM`,
`FilterBank`, `AugmentedDataset`), SSVEP estimators, pyriemann as a hard dependency, braindecode as an extra.

**Complaints.** "Ship the reference benchmark pipelines in the package, with an accessor" (they are outside the
wheel); Keras pipelines skipping datasets silently; pyriemann in the main dependencies.

**MOECoG.**
- Copy the YAML format and `load_pipelines`. Done.
- Improve: the reference YAMLs ship inside the wheel (`moecog/pipelines/configs/`) and `load_pipelines()` with
  no argument returns them; `$sfreq` placeholders make one file serve every sampling rate. This batch.
- Improve: a pipeline that cannot run on a dataset raises with the reason; nothing is skipped silently. This batch.
- Keep pyriemann optional (`moecog[riemann]`), braindecode optional (`moecog[deep]`). M2.

## 6. The benchmark entry point

**MOABB.** `moabb.benchmark(pipelines=, evaluations=, paradigms=, results=, overwrite=, output=, n_jobs=,
plot=, contexts=, include_datasets=, exclude_datasets=, n_splits=, cache_config=, optuna=, codecarbon_config=)`
with paradigm parameters supplied as `contexts/*.yml`.

**MOECoG.** `moecog.benchmark(datasets, paradigm, pipelines=, evaluations=, n_splits=, out=, overwrite=)`:
datasets by object or catalog id, paradigm by object or class name plus a context YAML, results appended to a
`ResultsStore`, and a reason printed for every (dataset, pipeline) pair that was skipped. This batch.

## 7. Statistics and plots

**MOABB.** `collapse_session_scores`, Wilcoxon and permutation paired tests per dataset, standardised effect
sizes, Stouffer combination across datasets (`combine_effects`, `combine_pvalues`),
`find_significant_differences`; `score_plot`, `paired_plot`, `summary_plot`, `meta_analysis_plot`, dataset
bubble plots, emissions plots.

**Complaints.** The one-sided Wilcoxon tail is chosen from the mean difference rather than from the signed-rank
statistic (issue of 2026-09-04); no critical-difference diagram.

**MOECoG.**
- Copy the structure (`moecog.analysis.meta_analysis`, `moecog.analysis.plotting`). This batch.
- Improve: the paired test direction comes from the signed-rank statistic; per-patient effect sizes use the
  patient as the unit (never the fold); a critical-difference ranking across pipelines is the default summary
  figure because ECoG benchmarks have few patients and many pipelines. This batch (ranking), M2 (CD diagram).

## 8. Caching and configuration

**MOABB.** `set_download_dir` writes `MNE_DATA` into the MNE config; `set_log_level`; `CacheConfig` stores
preprocessed BIDS derivatives next to the data.

**MOECoG.** `moecog.set_data_dir` / `get_data_dir` / `set_log_level` backed by `~/.moecog/config.json` with the
`MOECOG_DATA_DIR` environment variable taking precedence (Athene and laptops share code, not paths). This batch.
Preprocessed caches: M3, as parquet arrays keyed by paradigm digest, not BIDS derivatives.

## 9. Documentation and examples

**MOABB.** Sphinx with the pydata theme, an API page organised by concept, a sphinx-gallery of about 40 runnable
examples (tutorials, paradigm examples, data management, benchmarking, learning curves), `whats_new.rst` with
PR numbers and author links, install pages, a "paper results" page with DataTables, a dataset summary page.

**Complaints.** Generated documentation categories wrong, broken links (a recurring automated issue),
no dev/stable split.

**MOECoG.** MkDocs (material) with mkdocstrings for the API, the existing Markdown docs as pages, the dataset
atlas and smoke table as generated pages, a small gallery of runnable scripts under `examples/`, `CHANGELOG.md`
as the what's-new. Built on every push, deployed to GitHub Pages once the repository setting is enabled. M1
(this batch adds the site and workflow).

## 10. CI and quality

**MOABB.** Tests on Python 3.10-3.14 across three operating systems with a data cache, a docs build, a monthly
download test, a weekly link check, a what's-new check on every PR, pre-commit with black/isort/flake8/prettier
and pre-commit.ci, codecov.

**MOECoG.** Tests on 3.10-3.12 (ubuntu, macOS), ruff only, a changelog check on PRs, a weekly link check, a
monthly download test that smoke-tests two small public deposits, docs build. This batch. Windows and 3.13 when
someone needs them.

## 11. Community, governance, papers

**MOABB.** NeuroTechX umbrella, maintainers in `pyproject.toml`, a code of conduct, `CITATION.cff` with ORCIDs,
a Zenodo DOI per release, a JNE 2018 framework paper and a 2024 benchmark paper, dataset requests as issues
(dozens open), PapersWithCode links per dataset.

**MOECoG.** Maintainer Yifan Yu; versions cut on `yifan-study/MOECoG` and mirrored to the public `epyifany`
account; a Zenodo DOI once releases exist; a framework paper after M2, a benchmark paper after M3 (the order
MOABB used). Dataset requests use the issue template; the outreach list is private.

## Summary table

| component | MOABB | MOECoG decision | status |
|---|---|---|---|
| dataset contract | `get_data` nesting, codes, cache | copy + string subjects + electrode info + status registry | done |
| paradigms | per BCI family, classification only | classification and regression bases, explicit raw steps | done |
| within-session CV | stratified shuffled | chronological contiguous with fallback, fold policy recorded | done |
| cross-session | leave-one-session-out | copy | this batch |
| cross-subject | concatenate subjects | explicit aligner or refuse | M4 |
| learning curves | `LearningCurveSplitter` | copy | M2 |
| results | HDF5 keyed by repr digest | CSV keyed by params digest, incremental | this batch |
| pipelines | YAML outside the wheel | YAML inside the wheel, `$sfreq`, loud skips | this batch |
| benchmark() | one call | one call, catalog ids, contexts | this batch |
| statistics | Wilcoxon/permutation + Stouffer | same, tail from the statistic, patient as unit, ranking | this batch |
| plots | score, paired, summary, meta | score, paired, summary; CD diagram later | this batch |
| config | MNE config `MNE_DATA` | `~/.moecog/config.json` + env var | this batch |
| docs | Sphinx + gallery + GitHub Pages | MkDocs + examples + GitHub Pages | this batch |
| CI | 3 OS, 5 Pythons, download test, links, what's new | 2 OS, 3 Pythons, download test, links, changelog | this batch |
| releases | PyPI + Zenodo | tags on yifan-study, mirror to epyifany, PyPI on approval | v0.2.0 next |
