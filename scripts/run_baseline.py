#!/usr/bin/env python3
"""Run the reference baselines on one Miller experiment and write a CSV.

Examples::

    python scripts/run_baseline.py --experiment motor_basic --paradigm motor
    python scripts/run_baseline.py --experiment faces_basic --paradigm faces --subjects wc zt
    python scripts/run_baseline.py --experiment fingerflex --paradigm fingerflex --subjects bp

Set ``MOECOG_MILLER_DIR`` to an existing copy of the library; otherwise the
experiment zip is downloaded to ``$MOECOG_DATA_DIR/miller2019``.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from moecog.datasets import MillerLibrary
from moecog.evaluations import WithinSubjectCV
from moecog.paradigms import (
    CursorRegression,
    FaceHouseClassification,
    FingerClassification,
    FingerFlexionRegression,
    MotorClassification,
    NBackTargetClassification,
    VisualSearchClassification,
)
from moecog.pipelines import classification_baselines, regression_baselines

PARADIGMS = {
    "motor": MotorClassification,
    "finger": FingerClassification,
    "faces": FaceHouseClassification,
    "visual": VisualSearchClassification,
    "nback": NBackTargetClassification,
    "fingerflex": FingerFlexionRegression,
    "cursor": CursorRegression,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--paradigm", required=True, choices=sorted(PARADIGMS))
    ap.add_argument("--subjects", nargs="*", default=None)
    ap.add_argument("--pipelines", nargs="*", default=None, help="subset of the baseline names")
    ap.add_argument("--n-splits", type=int, default=5)
    ap.add_argument("--shuffle", action="store_true", help="stratified shuffled folds")
    ap.add_argument("--resample", type=float, default=None)
    ap.add_argument("--out", default=None, help="CSV path (default results/<exp>_<paradigm>.csv)")
    args = ap.parse_args()

    dataset = MillerLibrary(args.experiment)
    paradigm = PARADIGMS[args.paradigm](resample=args.resample)
    if not paradigm.is_valid(dataset):
        raise SystemExit(f"{args.paradigm} is not valid for {args.experiment}")
    sfreq = args.resample or dataset.sfreq
    is_reg = args.paradigm in ("fingerflex", "cursor")
    pipelines = regression_baselines(sfreq) if is_reg else classification_baselines(sfreq)
    if args.pipelines:
        pipelines = {k: v for k, v in pipelines.items() if k in args.pipelines}

    t0 = time.time()
    ev = WithinSubjectCV(paradigm, [dataset], n_splits=args.n_splits, shuffle=args.shuffle)
    res = ev.process(pipelines, subjects=args.subjects)
    out = Path(args.out or f"results/{args.experiment}_{args.paradigm}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out, index=False)

    table = (res.groupby(["pipeline", "metric", "subject"])["score"].mean()
             .unstack("subject").round(3))
    print(table.to_string())
    print("\nmean over subjects:")
    print(res.groupby(["pipeline", "metric"])["score"].mean().round(3).to_string())
    print(f"\n{len(res)} rows -> {out} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
