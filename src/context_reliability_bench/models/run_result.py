from __future__ import annotations

from dataclasses import dataclass

from context_reliability_bench.models.metric_result import MetricResult


@dataclass(frozen=True)
class RunResult:
    run_id: str
    metric_results: tuple[MetricResult, ...]
    seed: int | None = None
