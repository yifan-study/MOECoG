# Changelog

## 0.2.0.dev0 (unreleased, started 2026-09-09)

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
