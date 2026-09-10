#!/usr/bin/env python3
"""Smoke-test catalog entries: download a subset, load one subject, report.

Each entry of ``moecog.catalog.ENTRIES`` names a loader factory and a subset
spec. For every requested entry this script writes ``results/smoke/<id>.json``
with what was found (subjects, channels, sampling rate, duration, annotation
classes, electrode coordinates) and, when a paradigm applies and the data hold
at least two classes, a quick LogBandPower+LDA kappa on the first subject.

Usage::

    python scripts/smoke_test.py --ids ds005953 dandi-001535 --out results/smoke
    python scripts/smoke_test.py --all --tier openneuro
"""

from __future__ import annotations

import argparse
import json
import time
import traceback
import warnings
from pathlib import Path


warnings.filterwarnings("ignore")


def run_entry(entry, out_dir: Path, quick=True):
    t0 = time.time()
    rec = {"id": entry.id, "title": entry.title, "source": entry.source, "status": "ok",
           "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        ds = entry.build()
        rec["subjects_found"] = len(ds.subject_list)
        rec["subject_list"] = [str(s) for s in ds.subject_list[:20]]
        subject = ds.subject_list[0]
        data = ds.get_data(subjects=[subject])[subject]
        sessions = {}
        for ses, runs in data.items():
            for run, raw in runs.items():
                types = raw.get_channel_types()
                ann = list(raw.annotations.description)
                sessions[f"{ses}/{run}"] = {
                    "sfreq": float(raw.info["sfreq"]),
                    "n_ecog": int(sum(t == "ecog" for t in types)),
                    "n_misc": int(sum(t == "misc" for t in types)),
                    "duration_s": float(raw.times[-1]),
                    "n_annotations": len(ann),
                    "classes": {k: ann.count(k) for k in sorted(set(ann))[:15]},
                }
        rec["sessions"] = sessions
        try:
            einfo = ds.get_electrode_info(subject)
            rec["electrodes"] = {"n": int(einfo.positions.shape[0]), "frame": einfo.coord_frame}
        except Exception as e:  # noqa: BLE001
            rec["electrodes"] = f"none ({type(e).__name__})"
        rec["event_id"] = ds.event_id
        if quick and entry.paradigm is not None and ds.event_id and len(ds.event_id) >= 2:
            from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler

            from moecog.evaluations import WithinSubjectCV
            from moecog.pipelines.features import LogBandPower

            paradigm = entry.paradigm()
            if paradigm.is_valid(ds):
                first_raw = next(iter(next(iter(data.values())).values()))
                pipes = {"LogBandPower+LDA": make_pipeline(
                    LogBandPower(sfreq=paradigm.resample or first_raw.info["sfreq"]),
                    StandardScaler(), LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto"))}
                res = WithinSubjectCV(paradigm, [ds], n_splits=min(5, 3)).process(pipes, subjects=[subject])
                head = getattr(paradigm, "headline_metric", "kappa")
                rec["quick_baseline"] = {
                    "paradigm": type(paradigm).__name__, "metric": head,
                    "score": float(res[res.metric == head].score.mean()),
                    "n_trials": int(res.n_train.iloc[0] + res.n_test.iloc[0]),
                    "fold_policy": sorted(res.fold_policy.unique().tolist()),
                }
    except Exception as e:  # noqa: BLE001
        rec["status"] = "error"
        rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        rec["traceback"] = traceback.format_exc()[-1500:]
    rec["seconds"] = round(time.time() - t0, 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{entry.id}.json").write_text(json.dumps(rec, indent=1, default=str))
    return rec


def main():
    from moecog.catalog import ENTRIES

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--tier", default=None, help="restrict --all to a source tier (openneuro, dandi, ...)")
    ap.add_argument("--out", default="results/smoke")
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--skip-done", action="store_true", help="skip ids with an existing ok JSON")
    args = ap.parse_args()
    entries = list(ENTRIES.values()) if args.all else [ENTRIES[i] for i in (args.ids or [])]
    if args.tier:
        entries = [e for e in entries if e.source == args.tier]
    out = Path(args.out)
    for e in entries:
        f = out / f"{e.id}.json"
        if args.skip_done and f.is_file() and json.loads(f.read_text()).get("status") == "ok":
            print(f"skip {e.id}")
            continue
        rec = run_entry(e, out, quick=not args.no_baseline)
        status = rec["status"]
        extra = rec.get("error", "") if status != "ok" else json.dumps(rec.get("quick_baseline", {}))[:100]
        print(f"[{status}] {e.id} ({rec['seconds']}s) {extra}")


if __name__ == "__main__":
    main()
