#!/usr/bin/env python3
"""Build docs/leaderboard.md from the CSVs in results/.

Each CSV is the output of ``scripts/run_baseline.py`` (one row per dataset,
subject, session, pipeline, metric, fold). The leaderboard reports, per
(dataset, session-type, pipeline), the headline metric averaged first over
folds, then over subjects, with the standard deviation over subjects and the
number of subjects. Older CSVs without a ``fold_policy`` column are shown as
"chronological (legacy)".

Usage: python scripts/build_leaderboard.py [--results results] [--out docs/leaderboard.md]
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from pathlib import Path

import pandas as pd

HEADLINE = {"kappa", "pearson_r"}
ORDER = ["kappa", "accuracy", "balanced_accuracy", "pearson_r", "r2"]


def summarise(df):
    if "fold_policy" not in df.columns:
        df = df.assign(fold_policy="chronological (legacy)")
    if "evaluation" not in df.columns:
        df = df.assign(evaluation="within_subject")
    keys = ["dataset", "evaluation", "session", "pipeline", "metric", "subject"]
    per_subject = df.groupby(keys, observed=True)["score"].mean().reset_index()
    rows = []
    for (dataset, evaluation, session, pipeline), g in per_subject.groupby(["dataset", "evaluation", "session",
                                                                            "pipeline"]):
        entry = {"dataset": dataset, "evaluation": evaluation, "session": session, "pipeline": pipeline,
                 "n_subjects": g["subject"].nunique()}
        for metric, gm in g.groupby("metric"):
            entry[metric] = f"{gm['score'].mean():.3f} ± {gm['score'].std(ddof=0):.3f}"
        pol = df[(df.dataset == dataset) & (df.session == session)]["fold_policy"].unique()
        entry["fold_policy"] = ", ".join(sorted(map(str, pol)))
        rows.append(entry)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="docs/leaderboard.md")
    args = ap.parse_args()
    files = sorted(Path(args.results).glob("*.csv"))
    if not files:
        raise SystemExit("no results/*.csv")
    frames = []
    for f in files:
        df = pd.read_csv(f)
        df["source_file"] = f.name
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    summ = summarise(df)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        commit = "unknown"
    lines = ["# MOECoG leaderboard", "",
             f"Generated {dt.date.today().isoformat()} from `results/*.csv` at commit `{commit}` "
             "by `scripts/build_leaderboard.py`. Values are mean ± sd over subjects of the "
             "per-subject fold mean. Headline metrics: kappa (trials), Pearson r (kinematics). "
             "Chronological folds unless noted; see `docs/baselines.md` for protocol details.", ""]
    for dataset, g in summ.groupby("dataset"):
        lines.append(f"## {dataset}")
        lines.append("")
        metrics = [m for m in ORDER if m in g.columns and g[m].notna().any()]
        lines.append("| evaluation | session | pipeline | n | " + " | ".join(metrics) + " | folds |")
        lines.append("|---|---|---|---|" + "---|" * len(metrics) + "---|")
        for _, r in g.sort_values(["evaluation", "session", "pipeline"]).iterrows():
            vals = " | ".join("" if pd.isna(r.get(m)) else str(r.get(m)) for m in metrics)
            lines.append(
                f"| {r.evaluation} | {r.session} | {r.pipeline} | {r.n_subjects} | {vals} | {r.fold_policy} |"
            )
        lines.append("")
    lines += ["## How to add a row", "",
              "Run `scripts/run_baseline.py` (or any script that writes the same columns) into "
              "`results/<experiment>_<paradigm>.csv`, then `python scripts/build_leaderboard.py` "
              "and commit both. External submissions: open a pull request with the CSV, the exact "
              "command, the package version and the random seeds.", ""]
    Path(args.out).write_text("\n".join(lines))
    print(f"wrote {args.out} ({len(summ)} rows)")


if __name__ == "__main__":
    main()
