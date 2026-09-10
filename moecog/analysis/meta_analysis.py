"""Paired statistics across patients and datasets (the MOABB meta-analysis, with the tail taken from the
signed-rank statistic and the patient as the unit of analysis).

Input is the tidy results frame produced by the evaluations: one row per (dataset, subject, session, pipeline,
metric, fold). Everything below first collapses folds and sessions to one score per (dataset, subject,
pipeline), because folds of one patient are not independent samples.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from scipy import stats


def collapse_scores(df: pd.DataFrame, metric: str | None = None) -> pd.DataFrame:
    """One score per (dataset, subject, pipeline): the mean over folds and sessions of ``metric``."""
    if "metric" in df.columns:
        if metric is None:
            metric = "kappa" if (df["metric"] == "kappa").any() else df["metric"].iloc[0]
        df = df[df["metric"] == metric]
    return (df.groupby(["dataset", "subject", "pipeline"], sort=False)["score"].mean()
            .reset_index())


def _wide(scores: pd.DataFrame, dataset: str) -> pd.DataFrame:
    d = scores[scores["dataset"] == dataset]
    return d.pivot(index="subject", columns="pipeline", values="score").dropna(axis=0, how="any")


def paired_wilcoxon(a, b):
    """One-sided p-value that ``a > b``, with the direction read from the signed-rank statistic.

    Returns ``(p_one_sided, direction)`` where direction is +1 when the positive ranks dominate.
    """
    d = np.asarray(a, float) - np.asarray(b, float)
    d = d[d != 0]
    if d.size < 2:
        return 1.0, 0
    ranks = stats.rankdata(np.abs(d))
    w_plus, w_minus = ranks[d > 0].sum(), ranks[d < 0].sum()
    direction = 1 if w_plus > w_minus else (-1 if w_minus > w_plus else 0)
    p_two = float(stats.wilcoxon(d, alternative="two-sided").pvalue)
    if direction == 0:
        return 1.0, 0
    return (p_two / 2 if direction > 0 else 1 - p_two / 2), direction


def paired_permutation(a, b, n_perms: int = 10000, seed: int = 0):
    """One-sided permutation (sign-flip) p-value that mean(a - b) > 0; exact when 2^n <= n_perms."""
    d = np.asarray(a, float) - np.asarray(b, float)
    n = d.size
    if n == 0:
        return 1.0
    observed = d.mean()
    if 2 ** n <= n_perms:
        signs = np.array(list(itertools.product([1, -1], repeat=n)))
    else:
        rng = np.random.default_rng(seed)
        signs = rng.choice([1, -1], size=(n_perms, n))
    null = (signs * d).mean(axis=1)
    return float((np.sum(null >= observed) + 1) / (len(null) + 1))


def effect_size(a, b) -> float:
    """Standardised mean difference of the paired differences (Cohen's d_z)."""
    d = np.asarray(a, float) - np.asarray(b, float)
    sd = d.std(ddof=1) if d.size > 1 else 0.0
    return float(d.mean() / sd) if sd > 0 else 0.0


def compute_dataset_statistics(df: pd.DataFrame, metric: str | None = None, perm_cutoff: int = 20,
                               seed: int = 0) -> pd.DataFrame:
    """For every dataset and ordered pipeline pair: one-sided p (pipe1 > pipe2), effect size and n patients.

    Wilcoxon signed-rank when the dataset has at least ``perm_cutoff`` patients, an exact/random sign-flip
    permutation test otherwise (small ECoG cohorts are the norm).
    """
    scores = collapse_scores(df, metric)
    rows = []
    for dataset in scores["dataset"].unique():
        wide = _wide(scores, dataset)
        pipes = list(wide.columns)
        n = len(wide)
        for p1, p2 in itertools.permutations(pipes, 2):
            a, b = wide[p1].to_numpy(), wide[p2].to_numpy()
            if n >= perm_cutoff:
                p, _ = paired_wilcoxon(a, b)
                method = "wilcoxon"
            else:
                p = paired_permutation(a, b, seed=seed)
                method = "permutation"
            rows.append({"dataset": dataset, "pipe1": p1, "pipe2": p2, "p": p, "smd": effect_size(a, b),
                         "nsub": n, "method": method})
    return pd.DataFrame(rows)


def combine_pvalues(p, nsubs) -> float:
    """Stouffer combination of one-sided p-values weighted by sqrt(n) per dataset."""
    p = np.clip(np.asarray(p, float), 1e-12, 1 - 1e-12)
    w = np.sqrt(np.asarray(nsubs, float))
    z = stats.norm.isf(p)
    return float(stats.norm.sf((w * z).sum() / np.sqrt((w ** 2).sum())))


def combine_effects(effects, nsubs) -> float:
    """Weighted mean of standardised effects, weights proportional to sqrt(n)."""
    w = np.sqrt(np.asarray(nsubs, float))
    return float((w * np.asarray(effects, float)).sum() / w.sum())


def find_significant_differences(df: pd.DataFrame, metric: str | None = None, perm_cutoff: int = 20):
    """Combine the per-dataset tests: returns ``(P, T)`` pipeline x pipeline frames.

    ``P[i, j]`` is the combined one-sided p-value that pipeline i beats pipeline j; ``T[i, j]`` the combined
    effect size. Datasets with a single patient contribute nothing.
    """
    st = compute_dataset_statistics(df, metric=metric, perm_cutoff=perm_cutoff)
    st = st[st["nsub"] > 1]
    pipes = sorted(set(st["pipe1"]) | set(st["pipe2"]))
    P = pd.DataFrame(1.0, index=pipes, columns=pipes)
    T = pd.DataFrame(0.0, index=pipes, columns=pipes)
    for (p1, p2), g in st.groupby(["pipe1", "pipe2"]):
        P.loc[p1, p2] = combine_pvalues(g["p"], g["nsub"])
        T.loc[p1, p2] = combine_effects(g["smd"], g["nsub"])
    return P, T


def rank_pipelines(df: pd.DataFrame, metric: str | None = None) -> pd.DataFrame:
    """Mean rank of every pipeline across (dataset, patient) pairs, 1 = best, plus a Friedman test."""
    scores = collapse_scores(df, metric)
    wide = scores.pivot_table(index=["dataset", "subject"], columns="pipeline", values="score").dropna()
    ranks = wide.rank(axis=1, ascending=False)
    out = pd.DataFrame({"pipeline": ranks.columns, "mean_rank": ranks.mean(axis=0).to_numpy(),
                        "mean_score": wide.mean(axis=0).to_numpy(), "n": len(wide)}).sort_values("mean_rank")
    if wide.shape[1] >= 3 and len(wide) >= 2:
        out.attrs["friedman_p"] = float(stats.friedmanchisquare(*[wide[c] for c in wide.columns]).pvalue)
    return out.reset_index(drop=True)
