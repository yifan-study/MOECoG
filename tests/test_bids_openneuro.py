"""BIDS-iEEG loader against a cached OpenNeuro dataset (slow; needs the download)."""

import os
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.slow

_DATA = Path(os.environ.get("MOECOG_DATA_DIR", "~/moecog_data")).expanduser()
_ROOT = _DATA / "openneuro" / "ds005953"


@pytest.mark.skipif(not (_ROOT / "dataset_description.json").is_file(),
                    reason="ds005953 not downloaded (run HermesVisualECoG() once)")
def test_hermes_visual_loads_and_decodes():
    from moecog.datasets import HermesVisualECoG
    from moecog.evaluations import WithinSubjectCV
    from moecog.paradigms import EpochedClassification
    from moecog.pipelines import classification_baselines

    ds = HermesVisualECoG(download=False)
    assert ds.subject_list == ["01", "02"]
    raw = ds.get_data(subjects=["01"])["01"]["01"]["visual_01"]
    assert sum(t == "ecog" for t in raw.get_channel_types()) == 118
    assert len(raw.annotations) == 420
    einfo = ds.get_electrode_info("01")
    assert einfo.positions.shape == (118, 3)
    paradigm = EpochedClassification(tmin=0.0, tmax=0.5, fmin=1.0, fmax=200.0)
    X, y, meta = paradigm.get_data(ds, subjects=["01"])
    assert X.shape[0] == 420 and len(np.unique(y)) == 8
    pipes = {"lbp": classification_baselines(sfreq=raw.info["sfreq"])["LogBandPower+LDA"]}
    res = WithinSubjectCV(paradigm, [ds], n_splits=5).process(pipes, subjects=["01"])
    assert res[res.metric == "kappa"].score.mean() > 0.5
