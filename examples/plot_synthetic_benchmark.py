"""
Benchmark on synthetic data
===========================

Runs the reference pipelines on a synthetic ECoG dataset with the one-call benchmark, then draws the
per-patient score plot and the pipeline ranking. Nothing is downloaded; it runs in seconds.
"""

import matplotlib.pyplot as plt

from moecog import benchmark
from moecog.analysis import ranking_plot, score_plot
from moecog.datasets import FakeECoGDataset
from moecog.paradigms import EpochedClassification

dataset = FakeECoGDataset(n_subjects=4, n_sessions=2, n_channels=16, sfreq=250.0, n_trials_per_class=20, seed=0)
paradigm = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=120.0)

results = benchmark(dataset, paradigm, evaluations=("within_subject", "cross_session"), n_splits=5, sfreq=250.0)
print(results.groupby(["evaluation", "pipeline"])["score"].mean())

score_plot(results[results.evaluation == "within_subject"])
ranking_plot(results[results.evaluation == "within_subject"])
plt.show()
