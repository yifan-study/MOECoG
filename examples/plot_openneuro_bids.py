"""
Any BIDS-iEEG dataset on OpenNeuro
==================================

``BIDSiEEGDataset`` downloads one subject of an OpenNeuro deposit and exposes it like any other MOECoG dataset.
Here: the Hermes visual ECoG set (ds005953, CC0, 0.6 GB), grating versus noise stimuli.
"""

from moecog import benchmark
from moecog.datasets.bids import BIDSiEEGDataset
from moecog.paradigms import EpochedClassification

dataset = BIDSiEEGDataset(openneuro_id="ds005953", include=["sub-01/*", "*.json", "*.tsv"], subjects=["01"],
                          channel_types=("ecog", "seeg"), interval=[0.0, 1.0], code="ds005953")
paradigm = EpochedClassification(tmin=0.0, tmax=1.0, fmin=1.0, fmax=150.0, resample=250.0)
results = benchmark(dataset, paradigm, n_splits=3, out="results/ds005953_visual.csv")
print(results[results.metric == "kappa"].groupby("pipeline")["score"].mean())
