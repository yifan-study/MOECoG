"""Results bookkeeping, statistics across patients and datasets, and figures."""

from .meta_analysis import (
    collapse_scores,
    combine_effects,
    combine_pvalues,
    compute_dataset_statistics,
    effect_size,
    find_significant_differences,
    paired_permutation,
    paired_wilcoxon,
    rank_pipelines,
)
from .plotting import learning_curve_plot, paired_plot, ranking_plot, score_plot, summary_plot
from .results import ResultsStore, paradigm_digest, pipeline_digest

__all__ = [
    "ResultsStore", "pipeline_digest", "paradigm_digest", "collapse_scores", "compute_dataset_statistics",
    "find_significant_differences", "rank_pipelines", "paired_wilcoxon", "paired_permutation", "effect_size",
    "combine_pvalues", "combine_effects", "score_plot", "paired_plot", "summary_plot", "ranking_plot",
    "learning_curve_plot",
]
