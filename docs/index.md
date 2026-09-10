# MOECoG

Mother of all ECoG Benchmarks: a MOABB-style framework for benchmarking decoders on public electrocorticography
and intracranial EEG datasets. Datasets download from their source, paradigms turn recordings into labelled trials
or continuous targets, evaluations split the data per patient, pipelines are scikit-learn estimators (YAML-described
reference pipelines ship in the package), and results are tidy CSV files that scripts turn into tables.

```bash
pip install -e ".[nwb,loaders]"
```

```python
from moecog import benchmark
from moecog.datasets import MillerLibrary
from moecog.paradigms import MotorClassification

df = benchmark(MillerLibrary("motor_basic"), MotorClassification(), out="results/motor_basic_motor.csv",
               evaluations=("within_subject",))
```

- `MOECOG_DATA_DIR` (or `moecog.set_data_dir`) says where downloads go; `MOECOG_MILLER_DIR` points at an existing
  copy of the Stanford/Miller library.
- Every catalog entry and whether it loads today: [Decodable datasets](decodable_datasets.md) and
  [Smoke tests](smoke_tests.md).
- Numbers on the reference tasks: [Leaderboard](leaderboard.md).
- What MOABB did and what MOECoG changes: [Review and decisions](moabb_review.md).
