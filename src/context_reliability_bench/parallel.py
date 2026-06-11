from __future__ import annotations

import concurrent.futures
from collections.abc import Sequence

from context_reliability_bench.batch import _build_metrics
from context_reliability_bench.config.model import BenchmarkConfig
from context_reliability_bench.loader import load_fixture
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.runner import run_benchmark


def _run_one(config: BenchmarkConfig) -> RunResult:
    """Execute a single BenchmarkConfig and return its RunResult."""
    from pathlib import Path

    cases = load_fixture(Path(config.fixture_path))
    metrics = _build_metrics(config)
    return run_benchmark(cases, metrics, run_id=config.run_id, seed=config.seed)


def run_parallel(
    configs: Sequence[BenchmarkConfig],
    max_workers: int | None = None,
) -> list[RunResult]:
    """Run benchmark configs in parallel using a thread pool.

    Returns results in the same order as the input configs, regardless of
    which tasks finish first.
    """
    if not configs:
        return []

    n = len(configs)
    results: list[RunResult | None] = [None] * n

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_idx = {
            pool.submit(_run_one, cfg): i for i, cfg in enumerate(configs)
        }
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            results[idx] = future.result()

    return [r for r in results if r is not None]
