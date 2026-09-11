#!/usr/bin/env python3
"""docs/analysis.md + docs/figures/: per-patient distributions, rankings and significant differences per task.

    python scripts/build_analysis.py --results results --out docs/analysis.md --figures docs/figures
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import pandas as pd

from moecog.analysis import (
    find_significant_differences,
    learning_curve_plot,
    rank_pipelines,
    score_plot,
    summary_plot,
)


def learning_curve_section(task, g, metric, figdir, figrel):
    """Table of mean score per pipeline and training fraction, the fraction reaching 90 % of the full score,
    and the learning-curve figure."""
    import matplotlib.pyplot as plt

    per = g.groupby(["pipeline", "train_fraction", "subject"], as_index=False).agg(
        score=("score", "mean"), n_train=("n_train", "median"))
    fractions = sorted(per["train_fraction"].unique())
    n_pat = per["subject"].nunique()
    lines = [f"## {task} (learning_curve, {metric}, {n_pat} patients)", "",
             "Train on the first 10/25/50/100 % of the non-test trials of every (patient, session), test on the "
             "fixed final 20 %. The last column is the smallest fraction whose mean reaches 90 % of the "
             "full-data mean.", "",
             "| pipeline | " + " | ".join(
                 f"{int(round(f * 100))} % (n={int(per[per.train_fraction == f]['n_train'].median())})"
                 for f in fractions) + " | 90 % of full at |",
             "|---|" + "---|" * (len(fractions) + 1)]
    full = per[per.train_fraction == fractions[-1]].groupby("pipeline")["score"].mean()
    order = full.sort_values(ascending=False).index
    for name in order:
        means = per[per.pipeline == name].groupby("train_fraction")["score"].mean()
        reach = next((f for f in fractions if means.get(f, -1) >= 0.9 * means[fractions[-1]]), fractions[-1])
        lines.append(f"| {name} | " + " | ".join(f"{means.get(f, float('nan')):.3f}" for f in fractions)
                     + f" | {int(round(reach * 100))} % |")
    lines.append("")
    fig = learning_curve_plot(g, metric)
    fig.suptitle(task)
    stem = f"{task}_learning_curve"
    fig.savefig(figdir / f"{stem}.png", dpi=110, bbox_inches="tight")
    plt.close("all")
    lines += [f"![{stem}]({figrel}/{stem}.png)", ""]
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--pattern", default="reference_*.csv")
    ap.add_argument("--out", default="docs/analysis.md")
    ap.add_argument("--figures", default="docs/figures")
    args = ap.parse_args()
    import matplotlib

    matplotlib.use("Agg")

    files = sorted(Path(args.results).glob(args.pattern))
    if not files:
        raise SystemExit(f"no {args.pattern} under {args.results}")
    figdir = Path(args.figures)
    figdir.mkdir(parents=True, exist_ok=True)
    lines = ["# Reference benchmark analysis", "",
             f"Generated {dt.date.today().isoformat()} by `scripts/build_analysis.py` from `results/{args.pattern}`. "
             "Scores are per patient (mean over folds); tests are paired across patients (sign-flip permutation "
             "below 20 patients, Wilcoxon signed-rank otherwise, one-sided, combined with Stouffer weights); "
             "effect sizes are Cohen's d_z of the paired differences. See `docs/moabb_review.md`, section 7.", ""]
    for f in files:
        df = pd.read_csv(f)
        task = f.stem.replace("reference_", "")
        metric = "pearson_r" if "pearson_r" in set(df["metric"]) else "kappa"
        for ev, g in df.groupby("evaluation"):
            g = g[g.metric == metric]
            if g.empty:
                continue
            if ev == "learning_curve":
                lines += learning_curve_section(task, g, metric, figdir, Path(args.figures).name)
                continue
            per_pat = g.groupby(["pipeline", "subject"])["score"].mean().reset_index()
            summ = per_pat.groupby("pipeline")["score"].agg(["mean", "std", "median", "count"]).sort_values(
                "mean", ascending=False)
            lines += [f"## {task} ({ev}, {metric}, {per_pat['subject'].nunique()} patients)", "",
                      "| pipeline | mean | sd | median | patients |", "|---|---|---|---|---|"]
            for p, r in summ.iterrows():
                lines.append(f"| {p} | {r['mean']:.3f} | {r['std']:.3f} | {r['median']:.3f} | {int(r['count'])} |")
            lines.append("")
            if per_pat["pipeline"].nunique() >= 2 and per_pat["subject"].nunique() >= 2:
                ranks = rank_pipelines(g, metric)
                fp = ranks.attrs.get("friedman_p")
                lines.append("Mean rank (1 = best)" + (f", Friedman p = {fp:.3g}" if fp is not None else "") + ": "
                             + ", ".join(f"{r.pipeline} {r.mean_rank:.2f}" for r in ranks.itertuples()))
                lines.append("")
                P, T = find_significant_differences(g, metric)
                sig = [(a, b, P.loc[a, b], T.loc[a, b]) for a in P.index for b in P.columns
                       if a != b and P.loc[a, b] < 0.05]
                if sig:
                    lines.append("Significant pairwise differences (row beats column, p < 0.05):")
                    lines.append("")
                    for a, b, p, t in sorted(sig, key=lambda x: x[2]):
                        lines.append(f"- {a} > {b}: p = {p:.3g}, d_z = {t:.2f}")
                else:
                    lines.append("No pairwise difference reaches p < 0.05.")
                lines.append("")
                stem = f"{task}_{ev}"
                fig = score_plot(g, metric)
                fig.savefig(figdir / f"{stem}_scores.png", dpi=110)
                fig2 = summary_plot(P, T)
                fig2.savefig(figdir / f"{stem}_summary.png", dpi=110)
                import matplotlib.pyplot as plt

                plt.close("all")
                lines += [f"![{stem} scores]({Path(args.figures).name}/{stem}_scores.png)", "",
                          f"![{stem} summary]({Path(args.figures).name}/{stem}_summary.png)", ""]
    Path(args.out).write_text("\n".join(lines))
    print(f"wrote {args.out} and figures in {figdir}")


if __name__ == "__main__":
    main()
