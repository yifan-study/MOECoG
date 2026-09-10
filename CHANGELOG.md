# Changelog

## 0.2.0.dev0 (unreleased, started 2026-09-09)

The classification tier that PACE (paper #2) cut on 2026-07-17.

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
