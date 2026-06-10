from __future__ import annotations

from context_reliability_bench.models.run_result import RunResult


def aggregate_score(result: RunResult) -> float:
    """Mean of all metric means across a RunResult."""
    if not result.metric_results:
        return 0.0
    return (
        sum(mr.mean for mr in result.metric_results)
        / len(result.metric_results)
    )
