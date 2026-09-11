"""MOECoG — Mother of All ECoG Benchmarks.

A MOABB-style benchmarking framework for electrocorticographic (ECoG) motor decoding.
"""

__version__ = "0.3.0.dev0"


def benchmark(*args, **kwargs):
    """See :func:`moecog.benchmark.benchmark` (imported lazily to keep ``import moecog`` light)."""
    from .benchmark import benchmark as _benchmark

    return _benchmark(*args, **kwargs)


from .utils import get_data_dir, set_data_dir, set_log_level  # noqa: E402

__all__ = ["__version__", "benchmark", "get_data_dir", "set_data_dir", "set_log_level"]
