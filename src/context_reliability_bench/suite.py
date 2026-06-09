from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from context_reliability_bench.categories.contradiction import ContradictionCategory
from context_reliability_bench.categories.distractor import DistractorCategory
from context_reliability_bench.categories.noise_resistance import (
    NoiseResistanceCategory,
)
from context_reliability_bench.categories.registry import CategoryRegistry
from context_reliability_bench.categories.temporal_relevance import (
    TemporalRelevanceCategory,
)
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.runner import run_benchmark


@dataclass(frozen=True)
class SuiteResult:
    category_results: tuple[tuple[str, RunResult], ...]

    def get(self, name: str) -> RunResult | None:
        for n, r in self.category_results:
            if n == name:
                return r
        return None

    def names(self) -> list[str]:
        return [n for n, _ in self.category_results]


def build_default_registry() -> CategoryRegistry:
    registry = CategoryRegistry()
    registry.register(NoiseResistanceCategory())
    registry.register(ContradictionCategory())
    registry.register(TemporalRelevanceCategory())
    registry.register(DistractorCategory())
    return registry


def run_suite(
    registry: CategoryRegistry,
    metrics: Sequence[Metric],
) -> SuiteResult:
    if not metrics:
        raise ValueError("metrics must not be empty")
    results: list[tuple[str, RunResult]] = []
    for category in registry.categories():
        cases = category.load_cases()
        run_result = run_benchmark(cases, metrics, run_id=category.name)
        results.append((category.name, run_result))
    return SuiteResult(category_results=tuple(results))
