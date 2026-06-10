from __future__ import annotations

import math
from dataclasses import dataclass

from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult


@dataclass(frozen=True)
class MetricStats:
    metric_name: str
    minimum: float
    maximum: float
    mean: float
    median: float
    std_dev: float


def compute_metric_stats(mr: MetricResult) -> MetricStats:
    scores = [s for _, s in mr.case_scores]
    if not scores:
        return MetricStats(
            metric_name=mr.metric_name,
            minimum=0.0,
            maximum=0.0,
            mean=0.0,
            median=0.0,
            std_dev=0.0,
        )
    minimum = min(scores)
    maximum = max(scores)
    mean = sum(scores) / len(scores)
    return MetricStats(
        metric_name=mr.metric_name,
        minimum=minimum,
        maximum=maximum,
        mean=mean,
        median=_median(scores),
        std_dev=_std_dev(scores, mean),
    )


def run_stats(result: RunResult) -> tuple[MetricStats, ...]:
    return tuple(compute_metric_stats(mr) for mr in result.metric_results)


def _median(values: list[float]) -> float:
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0
    return sorted_vals[mid]


def _std_dev(values: list[float], mean: float) -> float:
    if len(values) <= 1:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)
