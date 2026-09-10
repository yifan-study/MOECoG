## What this changes

<!-- one paragraph: dataset / paradigm / pipeline / result / fix -->

## Checklist

- [ ] `ruff check moecog scripts tests` and `pytest -m "not slow"` pass locally
- [ ] new loaders have a catalog entry and a smoke-test JSON (`scripts/smoke_test.py --ids <id>`)
- [ ] new pipelines are described in `pipelines/*.yml` with a citation
- [ ] results were produced by `scripts/run_baseline.py` (seed, folds and version in the CSV) and the leaderboard regenerated
- [ ] no data files, credentials, or numbers from datasets under a data-use agreement
- [ ] `CHANGELOG.md` has a line under the unreleased version

Closes #
