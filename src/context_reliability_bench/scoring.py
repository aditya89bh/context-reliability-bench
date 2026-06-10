from __future__ import annotations

from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.suite import SuiteResult


def aggregate_score(result: RunResult) -> float:
    """Mean of all metric means across a RunResult."""
    if not result.metric_results:
        return 0.0
    return (
        sum(mr.mean for mr in result.metric_results)
        / len(result.metric_results)
    )


def category_scores(suite_result: SuiteResult) -> dict[str, float]:
    """Aggregate score per category from a SuiteResult."""
    return {
        name: aggregate_score(run)
        for name, run in suite_result.category_results
    }
