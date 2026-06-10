from __future__ import annotations

from dataclasses import dataclass

from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.suite import SuiteResult


@dataclass(frozen=True)
class MetricWeight:
    metric_name: str
    weight: float


@dataclass(frozen=True)
class WeightedScoringConfig:
    weights: tuple[MetricWeight, ...]
    default_weight: float = 1.0

    def get_weight(self, metric_name: str) -> float:
        for mw in self.weights:
            if mw.metric_name == metric_name:
                return mw.weight
        return self.default_weight


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


def weighted_score(
    result: RunResult,
    config: WeightedScoringConfig,
) -> float:
    """Weighted mean of metric scores using the provided config."""
    if not result.metric_results:
        return 0.0
    total_weight = 0.0
    weighted_sum = 0.0
    for mr in result.metric_results:
        w = config.get_weight(mr.metric_name)
        weighted_sum += mr.mean * w
        total_weight += w
    if total_weight == 0.0:
        return 0.0
    return weighted_sum / total_weight


def weighted_category_scores(
    suite_result: SuiteResult,
    config: WeightedScoringConfig,
) -> dict[str, float]:
    """Weighted aggregate score per category from a SuiteResult."""
    return {
        name: weighted_score(run, config)
        for name, run in suite_result.category_results
    }
