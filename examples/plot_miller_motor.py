"""
Hand versus tongue on the Miller library
========================================

The first real benchmark: cued hand and tongue movements of the Stanford/Miller ``motor_basic`` experiment,
19 patients, chronological folds, kappa. Downloads the library files on first use (or set
``MOECOG_MILLER_DIR`` to an existing copy).
"""

import matplotlib.pyplot as plt

from moecog import benchmark
from moecog.analysis import find_significant_differences, score_plot, summary_plot
from moecog.datasets import MillerLibrary
from moecog.paradigms import MotorClassification

results = benchmark(MillerLibrary("motor_basic"), MotorClassification(), out="results/motor_basic_motor.csv")
kappa = results[(results.metric == "kappa") & (results.evaluation == "within_subject")]
print(kappa.groupby("pipeline")["score"].agg(["mean", "std"]))

score_plot(kappa)
P, T = find_significant_differences(kappa)
summary_plot(P, T)
plt.show()
