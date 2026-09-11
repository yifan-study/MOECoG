"""
Learning curves on synthetic data
=================================

How much of a patient's session does each pipeline need? ``LearningCurveEvaluation`` keeps the last fifth of
every (patient, session) as the test block and trains on the first 10, 25, 50 and 100 % of the remaining
trials in recording order, the way a calibration phase grows. Nothing is downloaded; it runs in seconds.
"""

import matplotlib.pyplot as plt

from moecog import benchmark
from moecog.analysis import learning_curve_plot
from moecog.datasets import FakeECoGDataset
from moecog.paradigms import EpochedClassification

dataset = FakeECoGDataset(n_subjects=4, n_sessions=1, n_channels=16, sfreq=250.0, n_trials_per_class=40, seed=0)
paradigm = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=120.0)

results = benchmark(dataset, paradigm, evaluations=("learning_curve",), sfreq=250.0)
kappa = results[results.metric == "kappa"]
print(kappa.groupby(["pipeline", "train_fraction"])["score"].mean().unstack().round(2))

learning_curve_plot(kappa, "kappa")
plt.show()
