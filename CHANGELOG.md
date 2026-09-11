# Changelog

## 0.3.0.dev0 (unreleased)

- `LearningCurveEvaluation` (`evaluations=("learning_curve",)` in `benchmark()`):
  train on the first 10/25/50/100 % of a patient's non-test trials in recording
  order, test on the fixed final 20 %; rows carry `train_fraction` and `n_train`;
  `learning_curve_plot()` and a learning-curve section in `docs/analysis.md`.
- Two more Riemannian reference pipelines: `Riemann HG TS + LogReg` (covariances of
  the 70-150 Hz band-passed epochs, the Riemannian counterpart of log band power,
  through the new `BandPassFilter` transformer) and `Riemann Env TS + LogReg`
  (pyriemann `ERPCovariances` prototypes of log high-gamma envelopes).
- A pipeline that raises on one fold now costs only its own rows (warning names the
  pipeline, patient and fold; the rows stay "not yet computed" and are retried);
  before, the exception dropped every pipeline of that patient.
- `HilbertEnvelope`: the envelope is floored at zero before the log; zero-phase
  decimation rang below zero on tiny envelopes and produced NaN features.
- `scripts/run_reference.py --evaluations ...` overrides a task's evaluations.

- `docs/best_practices.md`: literature pass on preprocessing, transfer (alignment,
  HTNet, stability across days, pretrained representations, Neuroprobe) and
  evaluation practices, with the roadmap chunks each point feeds.
- M2 pipelines: Riemannian tangent space (`riemann` extra) and braindecode
  `ShallowFBCSPNet` through `moecog.pipelines.deep.BraindecodeClassifier`;
  `load_pipelines()` reports pipelines skipped for a missing optional
  dependency; `scripts/run_reference.py`, `scripts/build_analysis.py`,
  leaderboard grouped by evaluation. ShallowFBCSPNet budget set to 150 epochs of
  batch 16 after a probe (40 x 32 gave kappa 0.22 vs 0.40 on three patients).
- BCI Competition III-1 loads its test session with the published labels;
  cross-session (train -> test, a week apart) is part of the reference runs.

## 0.2.0 (2026-09-10)

Published to PyPI (`pip install moecog`) and tagged `v0.2.0` on yifan-study/MOECoG.

The classification tier that PACE (paper #2) cut on 2026-07-17, plus the
widening to every obtainable intracranial dataset (2026-09-10).

- `docs/dataset_catalog.md`: ~90 ECoG/iEEG datasets (public, by request,
  non-human, clinical) with access, size, published results, source
  preprocessing and a loader plan; raw repository snapshots in `docs/catalog/`.
- `docs/preprocessing_catalog.md` and `moecog.preprocessing`: referencing,
  notch, Hilbert envelopes, the Chang-lab high-gamma preset; paradigms accept
  `raw_steps`.
- `BIDSiEEGDataset`: generic BIDS-iEEG loader with OpenNeuro download and
  named datasets (Hermes visual, Podcast, film, Visual ECoG).
- `WithinSubjectCV` fold policy (PRSNL-67): chronological folds with a
  stratified fallback for block-ordered files; kappa is the headline metric.
- `results/` + `scripts/build_leaderboard.py` -> `docs/leaderboard.md`.
- Catalog registry (`moecog.catalog`) and smoke sweep (`scripts/smoke_test.py`,
  `scripts/build_smoke_table.py`, `docs/smoke_tests.md`): every reachable catalog
  entry is downloaded as a one-subject subset, loaded and scored (2026-09-10).
- Loaders: `DANDIDataset`/`read_nwb_raw`; BCI Competition IV-4 and III-1; Peterson
  naturalistic sets; Rogers µECoG; Verwoert iBIDS; Merk Dataverse (BIDS rebuild);
  Du-IN; SWEC; Omni-iEEG EDF; mindeye iEEG NSD derivatives; Brain Treebank.
- BIDS loader hardening from the sweep: recursive subject downloads, NWB inside
  BIDS, EEG-typed intracranial channels, channels.tsv mismatches, disjoint
  montages per run, union of bad channels per subject, direct reading when
  mne-bids fails; paradigms pick ECoG channels without the implicit bad-channel
  exclusion; datasets may deliver `mne.Epochs`.
- Sweep outcome (96 ok, 0 error, 12 unsupported, 22 blocked, 0 pending of 130 entries): the errors that remain are documented per entry
  in `docs/smoke_tests.md`. Unsupported: MEF3 (`.mefd`, needs pymef), NWB sets
  that hold sorted spikes or features without an `ElectricalSeries`,
  metadata-only OpenNeuro snapshots, one deleted dataset. Blocked: account or
  DUA sources, two OpenNeuro sets whose files return HTTP 403 (ds006254,
  ds007703).
- MOABB parity, batch 1 (2026-09-10, Yifan: "copy everything that moabb did
  but try to make them better"): `docs/moabb_review.md` (component-by-component
  decisions); `moecog.analysis` (`ResultsStore` CSV keyed by parameter digests
  with `not_yet_computed`; paired Wilcoxon with the tail from the signed-rank
  statistic, permutation tests, effect sizes, Stouffer combination,
  `find_significant_differences`, `rank_pipelines`; `score_plot`, `paired_plot`,
  `summary_plot`, `ranking_plot`); `CrossSessionEvaluation` (leave one session
  out, chronological) and `incompatibility_reason` on every evaluation;
  `moecog.benchmark` with several evaluations, paradigms by name with context
  YAML, incremental storage and loud skips; reference pipelines and contexts
  ship inside the wheel (`moecog/pipelines/configs`, `moecog/paradigms/contexts`);
  `moecog.set_data_dir` / `get_data_dir` / `set_log_level`; MkDocs site with
  API pages and workflows for docs, changelog check, link check and a monthly
  download test; `examples/`.
- Package and contribution path, following MOABB (2026-09-10, Yifan: "start
  MoEcog as a package and a contribution guideline"): `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `CITATION.cff`, issue and PR templates, pre-commit,
  GitHub Actions CI (ruff + synthetic tests on 3.10-3.12), `docs/moabb_lessons.md`,
  `ROADMAP.md` rewritten as milestones with definitions of done and a monthly
  re-evaluation. Pipelines as YAML (`pipelines/*.yml`,
  `moecog.pipelines.load_pipelines`) and a one-call `moecog.benchmark(...)`.
- Second pass on the unsupported and blocked entries (2026-09-10): MEF3 via
  `pymef` (seven OpenNeuro sets), GET-only OpenNeuro downloads through the
  GraphQL file tree (ds006254), BRAVO neural-feature trials (DANDI 001535),
  Bellier music HFA (Zenodo), Stolk sensorimotor trials (OSF), the Li tonal
  speech set from ScienceDB (`moecog.datasets.scidb`); 106 ok, 2 error, 3 unsupported, 19 blocked, 0 pending of 130 entries.
- `docs/decodable_datasets.md` / `.json` / `.html` (`scripts/build_dataset_list.py`,
  `scripts/build_dataset_page.py`): every catalog entry with size, subjects,
  first-run channels and rate, licence, decoding target, label kind, which of
  our decoder lines apply, and load status; grouped by task family.
- Loader fixes found only on real files: Du-IN pickles (`utils.DotDict`),
  Blosc-compressed SWEC HDF5 (`hdf5plugin`, new `loaders` extra), the Verwoert
  OSF archive (direct file download; the project-level zip export nests the
  archive under its own name), resumable `_download` with size checks,
  `BIDSiEEGDataset(max_runs=N)` so hour-long multi-run subjects (RAM ds0055xx)
  fit in memory, session-level subsets for longitudinal sets (ds006890).

- `MillerLibrary(experiment=...)`: registry-driven loader for all 16
  Stanford/Miller experiments (204 files). Cue codes become MNE annotations;
  dataglove, cursor, task and coherence traces become misc channels; electrode
  coordinates are read from the per-experiment location files. Downloads with
  MD5 checks; `MOECOG_MILLER_DIR` points at an existing copy.
- `docs/miller_library_map.md` and `scripts/inventory_miller_library.py`: the
  map of where every experiment's trials and labels live.
- `FakeECoGDataset` for tests and examples.
- Paradigms: `EpochedClassification` and named presets (motor, finger,
  face/house, visual search, n-back target), `FingerFlexionRegression`,
  `CursorRegression` (velocity by default).
- `WithinSubjectCV` with chronological folds and a purge gap for regression.
- `LogBandPower`, `HighGammaPower`, reference baseline pipelines.
- `ElectrodeInfo` gained `coord_frame` and `region_code`; subject ids may be
  strings.

## 0.1.0 (2026-02-09)

Package scaffold: base classes for datasets, paradigms, evaluations.
