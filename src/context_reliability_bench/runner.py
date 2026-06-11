from __future__ import annotations

import random
from collections.abc import Sequence

from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.timing import BenchmarkTiming, TimingRecord, _Timer


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

    timing_records: list[TimingRecord] = []
    total_timer = _Timer()
    with total_timer:
        metric_results: list[MetricResult] = []
        for metric in metrics:
            metric_timer = _Timer()
            with metric_timer:
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
            timing_records.append(
                TimingRecord(
                    label=metric.name,
                    elapsed_seconds=metric_timer.elapsed,
                )
            )

    timing_records.append(
        TimingRecord(label="total", elapsed_seconds=total_timer.elapsed)
    )

    return RunResult(
        run_id=run_id,
        metric_results=tuple(metric_results),
        seed=seed,
        timing=BenchmarkTiming(records=tuple(timing_records)),
    )
