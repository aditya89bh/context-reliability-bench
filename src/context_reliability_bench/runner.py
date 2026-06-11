from __future__ import annotations

import random
from collections.abc import Sequence

from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult


def run_benchmark(
    cases: Sequence[BenchmarkCase],
    metrics: Sequence[Metric],
    run_id: str = "default",
    seed: int | None = None,
) -> RunResult:
    if not cases:
        raise ValueError("cases must not be empty")
    if not metrics:
        raise ValueError("metrics must not be empty")

    ordered: list[BenchmarkCase] = list(cases)
    if seed is not None:
        random.Random(seed).shuffle(ordered)

    metric_results: list[MetricResult] = []
    for metric in metrics:
        case_scores: list[tuple[str, float]] = []
        for case in ordered:
            score = metric.compute(case.context, case.relevant_doc_ids)
            case_scores.append((case.id, score))
        mean = sum(s for _, s in case_scores) / len(case_scores)
        metric_results.append(
            MetricResult(
                metric_name=metric.name,
                case_scores=tuple(case_scores),
                mean=mean,
            )
        )

    return RunResult(
        run_id=run_id,
        metric_results=tuple(metric_results),
        seed=seed,
    )
