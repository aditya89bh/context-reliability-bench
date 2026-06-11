from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from context_reliability_bench.models.metric_result import MetricResult


@dataclass(frozen=True)
class RunResult:
    run_id: str
    metric_results: tuple[MetricResult, ...]
    seed: int | None = None
    # ReproducibilityMetadata stored as Any to avoid circular imports;
    # type is context_reliability_bench.reproducibility.ReproducibilityMetadata
    reproducibility: Any = None
    # BenchmarkTiming stored as Any to avoid circular imports;
    # type is context_reliability_bench.timing.BenchmarkTiming
    timing: Any = None
