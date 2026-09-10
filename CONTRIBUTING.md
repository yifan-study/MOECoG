# Contributing to MOECoG

MOECoG (Mother of all ECoG Benchmarks) follows the model that made [MOABB](https://github.com/NeuroTechX/moabb)
work for EEG: a BSD-licensed Python package, datasets and pipelines added one pull request at a time, results
that anyone can regenerate, and a public table that says which combinations have actually been run. You do not
need to bring a whole dataset family or a new decoder architecture. One loader, one pipeline, one verified
result, or one corrected row in a table is a contribution.

By participating you agree to the [code of conduct](CODE_OF_CONDUCT.md).

## What you can contribute

| kind | what it is | where it goes | definition of done |
|---|---|---|---|
| dataset | a loader for a public ECoG/iEEG deposit | `moecog/datasets/`, entry in `moecog/catalog.py` | smoke test passes (`scripts/smoke_test.py --ids <id>`), row in `docs/smoke_tests.md`, licence and access noted |
| paradigm | a way of turning recordings into labelled trials or targets | `moecog/paradigms/` | works on `FakeECoGDataset`, documented `headline_metric`, test in `tests/` |
| pipeline | a scikit-learn pipeline (features + estimator), optionally a braindecode model | `moecog/pipelines/configs/*.yml` (shipped in the wheel) or `moecog/pipelines/` | YAML parses with `moecog.pipelines.load_pipelines`, cites its paper, runs on one real dataset |
| result | numbers from `moecog.benchmark(...)` or `scripts/run_baseline.py` | `results/*.csv` (a `ResultsStore`: digests, version, timestamp per row), regenerated `docs/leaderboard.md` | seeds, folds and package version recorded in the CSV; no data under a DUA |
| fix or docs | anything that makes the above clearer or truer | | tests still pass |

Things we will not merge: data files (loaders download from the source), credentials, results on datasets whose
licence forbids redistribution of derived numbers, or numbers that cannot be regenerated from the repository.

## Set up

```bash
git clone https://github.com/yifan-study/MOECoG.git
cd MOECoG
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # loaders, deep, viz, anatomy, pytest, ruff
pre-commit install               # optional: runs ruff on commit
pytest -m "not slow"             # 40 tests, synthetic data only, under 10 s
```

Real-data tests are marked `slow` and need `MOECOG_MILLER_DIR` (Miller library) or a network connection.
`MOECOG_DATA_DIR` sets where downloads land (default `~/moecog_data`).

## Workflow

1. Open an issue (or pick one). Dataset requests use the dataset template so licence and format are known up front.
2. Branch from `main`: `git checkout -b dataset/<name>` (or `pipeline/`, `fix/`, `docs/`).
3. Make the change with tests. `ruff check moecog scripts tests` and `pytest -m "not slow"` must pass.
4. Add a line to `CHANGELOG.md` under the unreleased version.
5. Open a pull request against `main` using the template. One topic per PR.
6. A maintainer reviews within a week. Small PRs merge fast; large ones get split.

## Adding a dataset

1. Find the deposit in `docs/dataset_catalog.md` (or add it there with source, licence, size, task).
2. Pick the loader path:
   - BIDS-iEEG on OpenNeuro: no code, add an entry to `moecog/catalog.py` (`_openneuro_entry`) and run the smoke test.
   - NWB on DANDI: `DANDIDataset(dandiset, include=..., max_asset_gb=...)`.
   - Anything else: subclass `BaseECoGDataset` (or `_SimpleDataset` in `moecog/datasets/misc.py`) and implement
     `data_path` (download, with `_download` for resumable transfers) and `_get_single_subject_data`, returning
     `{session: {run: mne.io.Raw | mne.Epochs}}` with ECoG channels typed `ecog`, other channels `misc`,
     and trials as annotations (or an `EpochsArray` with `event_id`).
3. Give the class `code`, `paradigm`, `interval`, `sfreq`, `doi`; implement `get_electrode_info` when coordinates ship.
4. Register it in `moecog/catalog.py` with a one-subject subset for the smoke test and a `paradigm` factory when trials exist.
5. Run `python scripts/smoke_test.py --ids <id>` and `python scripts/build_smoke_table.py`; commit the JSON and the table.
6. Add a row to `docs/decodable_datasets.md` through `scripts/build_dataset_list.py` (curated notes live in that script).

Gotchas we have already hit are listed in `docs/dataset_catalog.md` (smoke-test section) and the CHANGELOG: OSF
folder exports that nest a zip under its own name, Blosc-compressed HDF5, pickles that need a shim, MEF3, datasets
that refuse HEAD but serve GET, hour-long runs that need `max_runs` / `max_seconds`.

## Adding a pipeline

Pipelines are described as YAML so they can be cited and compared without reading code (the MOABB convention):

```yaml
name: LogBandPower + LDA
paradigms: [EpochedClassification, MotorClassification]
citations: [https://doi.org/10.1088/1741-2552/aadea0]
pipeline:
  - name: LogBandPower
    from: moecog.pipelines.features
    parameters: {sfreq: 1000}
  - name: StandardScaler
    from: sklearn.preprocessing
  - name: LinearDiscriminantAnalysis
    from: sklearn.discriminant_analysis
    parameters: {solver: lsqr, shrinkage: auto}
```

Put the file in `moecog/pipelines/configs/` (they ship inside the package, so `load_pipelines()` with no argument
returns them), check `moecog.pipelines.load_pipelines()` builds it, and run it on one dataset with
`moecog.benchmark(...)` or `scripts/run_baseline.py`. Grid search belongs inside the pipeline (`GridSearchCV` as a
step), never in the evaluation. Deep models go through braindecode (`moecog[deep]`) and must run on CPU for the tests.

## Adding results

`scripts/run_baseline.py --experiment motor_basic --paradigm motor --pipelines ... --out results/<name>.csv` writes
per-subject, per-fold rows with the fold policy, package version and seed. `scripts/build_leaderboard.py` turns
`results/*.csv` into `docs/leaderboard.md`. Report kappa for classification and Pearson r for regression, as the
paradigms define; never hand-edit the CSVs.

## Style

- Python 3.10+, ruff (line length 120), type hints where they help, docstrings that say what a function returns.
- No em-dashes in prose. Say what a thing is, then why.
- Tests are synthetic by default (`FakeECoGDataset`, generated NWB/MAT files); real data only behind `@pytest.mark.slow`.

## Maintainers

Yifan Yu (yifan-study). Decisions that need the project owner (licences, tiers, outreach) are tracked in the
private Jira project and summarised in `ROADMAP.md`.
