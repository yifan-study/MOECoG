"""Figures for benchmark results (matplotlib only, safe with the Agg backend)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .meta_analysis import collapse_scores, rank_pipelines


def _plt():
    import matplotlib

    if matplotlib.get_backend().lower() not in ("agg", "module://matplotlib_inline.backend_inline"):
        try:
            import matplotlib.pyplot as plt

            return plt
        except Exception:  # noqa: BLE001
            matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def score_plot(df: pd.DataFrame, metric: str | None = None, pipelines=None, axes=None):
    """Per-patient scores of every pipeline, one panel per dataset (points = patients, bar = median)."""
    plt = _plt()
    scores = collapse_scores(df, metric)
    if pipelines:
        scores = scores[scores["pipeline"].isin(pipelines)]
    datasets = list(scores["dataset"].unique())
    if axes is None:
        fig, axes = plt.subplots(1, len(datasets), figsize=(4 * len(datasets), 4), squeeze=False)
        axes = axes[0]
    else:
        fig = axes[0].figure
    for ax, ds in zip(axes, datasets):
        d = scores[scores["dataset"] == ds]
        pipes = list(d["pipeline"].unique())
        for i, p in enumerate(pipes):
            vals = d[d["pipeline"] == p]["score"].to_numpy()
            jitter = (np.random.default_rng(i).random(len(vals)) - 0.5) * 0.3
            ax.scatter(np.full(len(vals), i) + jitter, vals, s=18, alpha=0.7)
            ax.hlines(np.median(vals), i - 0.3, i + 0.3, color="black", lw=2)
        ax.set_xticks(range(len(pipes)))
        ax.set_xticklabels(pipes, rotation=30, ha="right", fontsize=8)
        ax.set_title(ds)
        ax.set_ylabel(metric or "score")
    fig.tight_layout()
    return fig


def paired_plot(df: pd.DataFrame, alg1: str, alg2: str, metric: str | None = None, ax=None):
    """Patient-by-patient comparison of two pipelines with the identity line."""
    plt = _plt()
    scores = collapse_scores(df, metric)
    wide = scores.pivot_table(index=["dataset", "subject"], columns="pipeline", values="score").dropna()
    if ax is None:
        fig, ax = plt.subplots(figsize=(4.5, 4.5))
    else:
        fig = ax.figure
    for ds, g in wide.groupby(level="dataset"):
        ax.scatter(g[alg2], g[alg1], s=22, alpha=0.8, label=str(ds))
    lo = min(wide[alg1].min(), wide[alg2].min())
    hi = max(wide[alg1].max(), wide[alg2].max())
    ax.plot([lo, hi], [lo, hi], color="grey", lw=1, ls="--")
    ax.set_xlabel(alg2)
    ax.set_ylabel(alg1)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def summary_plot(P: pd.DataFrame, T: pd.DataFrame, p_threshold: float = 0.05, ax=None):
    """Heat map of combined effect sizes; cells where row beats column at ``p_threshold`` are marked."""
    plt = _plt()
    if ax is None:
        fig, ax = plt.subplots(figsize=(1.2 * len(T) + 2, 1.0 * len(T) + 1.5))
    else:
        fig = ax.figure
    vmax = float(np.nanmax(np.abs(T.to_numpy()))) or 1.0
    im = ax.imshow(T.to_numpy(), cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    for i in range(len(T)):
        for j in range(len(T)):
            if i != j and P.iloc[i, j] < p_threshold:
                ax.text(j, i, "*", ha="center", va="center", fontsize=14)
    ax.set_xticks(range(len(T)))
    ax.set_xticklabels(T.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(T)))
    ax.set_yticklabels(T.index, fontsize=8)
    ax.set_title("effect of row over column (* p < %.2f)" % p_threshold, fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.04)
    fig.tight_layout()
    return fig


def ranking_plot(df: pd.DataFrame, metric: str | None = None, ax=None):
    """Mean rank per pipeline across (dataset, patient) pairs, best on top."""
    plt = _plt()
    r = rank_pipelines(df, metric)
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 0.5 * len(r) + 1.5))
    else:
        fig = ax.figure
    ax.barh(r["pipeline"][::-1], r["mean_rank"][::-1])
    ax.set_xlabel("mean rank (1 = best)")
    p = r.attrs.get("friedman_p")
    ax.set_title(f"n = {int(r['n'].iloc[0])} patients" + (f", Friedman p = {p:.3g}" if p is not None else ""),
                 fontsize=9)
    fig.tight_layout()
    return fig
