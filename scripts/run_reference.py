#!/usr/bin/env python3
"""Reference benchmark on the Miller tier (roadmap M2): tasks x pipelines with chronological folds.

    python scripts/run_reference.py --tasks motor_basic faces_basic --pipelines classical
    python scripts/run_reference.py --tasks motor_basic --pipelines deep --seeds 0 1 2 --resample 250

Results go to ``results/reference_<task>.csv`` (a ResultsStore, so reruns skip finished patients) and the
leaderboard is regenerated with ``scripts/build_leaderboard.py``. Set ``MOECOG_MILLER_DIR`` to an existing
copy of the library, otherwise the experiment zips are downloaded.
"""

from __future__ import annotations

import argparse
import time
import warnings

from moecog import benchmark
from moecog.datasets import MillerLibrary
from moecog.paradigms import (
    EpochedClassification,
    FaceHouseClassification,
    FingerFlexionRegression,
    MotorClassification,
)


def _miller(exp):
    return lambda: MillerLibrary(exp)


def _bci_iii_1():
    from moecog.datasets.misc import BCICompIII1

    return BCICompIII1()


# task -> (paradigm class name, paradigm factory(resample), dataset factory, evaluations)
TASKS = {
    "motor_basic": ("MotorClassification", lambda r: MotorClassification(resample=r), _miller("motor_basic"),
                    ("within_subject",)),
    "imagery_basic": ("MotorClassification", lambda r: MotorClassification(resample=r), _miller("imagery_basic"),
                      ("within_subject",)),
    "faces_basic": ("FaceHouseClassification", lambda r: FaceHouseClassification(resample=r),
                    _miller("faces_basic"), ("within_subject",)),
    "gestures": ("EpochedClassification", lambda r: EpochedClassification(tmin=0.0, tmax=None, fmin=1.0,
                                                                            fmax=200.0, resample=r),
                 _miller("gestures"), ("within_subject",)),
    "fingerflex": ("FingerFlexionRegression", lambda r: FingerFlexionRegression(resample=r),
                   _miller("fingerflex"), ("within_subject",)),
    # two sessions a week apart with published test labels: the one honest cross-session check in this tier
    "bci_iii_1": ("EpochedClassification", lambda r: EpochedClassification(tmin=0.0, tmax=None, fmin=1.0,
                                                                             fmax=200.0, resample=r),
                  _bci_iii_1, ("within_subject", "cross_session", "within_subject:ea", "cross_session:ea",
                               "cross_session:recenter", "cross_session:zscore")),
}
DEEP = "ShallowFBCSPNet"


def build_pipelines(kind, paradigm_name, sfreq, seeds):
    from moecog.pipelines import load_pipelines

    pipes = load_pipelines(sfreq=sfreq, paradigm=paradigm_name)
    classical = {k: v for k, v in pipes.items() if k != DEEP}
    if kind == "classical":
        return classical
    deep = {}
    if DEEP in pipes:
        for s in seeds:
            p = pipes[DEEP]
            from sklearn.base import clone

            q = clone(p)
            q.set_params(**{f"{q.steps[-1][0]}__random_state": int(s)})
            deep[f"{DEEP} s{s}"] = q
    else:
        warnings.warn("braindecode/torch not installed: no deep pipeline")
    return deep if kind == "deep" else {**classical, **deep}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", nargs="*", default=list(TASKS))
    ap.add_argument("--pipelines", choices=["classical", "deep", "all"], default="classical")
    ap.add_argument("--seeds", nargs="*", type=int, default=[0])
    ap.add_argument("--resample", type=float, default=None, help="paradigm resampling rate (Hz)")
    ap.add_argument("--subjects", nargs="*", default=None)
    ap.add_argument("--n-splits", type=int, default=5)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--evaluations", nargs="*", default=None,
                    help="override the task's evaluations, e.g. learning_curve (default: the task's tuple)")
    args = ap.parse_args()
    for task in args.tasks:
        pname, make, build, evaluations = TASKS[task]
        if args.evaluations:
            evaluations = tuple(args.evaluations)
        paradigm = make(args.resample)
        ds = build()
        sfreq = args.resample or 1000.0
        pipes = build_pipelines(args.pipelines, pname, sfreq, args.seeds)
        if not pipes:
            print(f"[{task}] no pipelines to run")
            continue
        t0 = time.time()
        df = benchmark(ds, paradigm, pipelines=pipes, n_splits=args.n_splits, subjects=args.subjects,
                       out=f"{args.out_dir}/reference_{task}.csv", overwrite=args.overwrite, sfreq=sfreq,
                       evaluations=evaluations)
        head = "pearson_r" if task == "fingerflex" else "kappa"
        print(f"[{task}] {time.time() - t0:.0f} s, {head} per pipeline (mean over folds and patients):")
        for ev in evaluations:
            sub = df[(df.metric == head) & (df.evaluation == ev)]
            if sub.empty:
                continue
            keys = ["pipeline", "train_fraction"] if ev == "learning_curve" else ["pipeline"]
            print(f"  {ev}:")
            print(sub.groupby(keys)["score"].agg(["mean", "std", "count"]).round(3).to_string())


if __name__ == "__main__":
    main()
