"""MOECoG — Mother of All ECoG Benchmarks.

A MOABB-style benchmarking framework for electrocorticographic (ECoG) motor decoding.
"""

__version__ = "0.2.0.dev0"


def benchmark(*args, **kwargs):
    """See :func:`moecog.benchmark.benchmark` (imported lazily to keep ``import moecog`` light)."""
    from .benchmark import benchmark as _benchmark

    return _benchmark(*args, **kwargs)


__all__ = ["__version__", "benchmark"]
