from __future__ import annotations

from pathlib import Path

from context_reliability_bench.categories.base import BenchmarkCategory
from context_reliability_bench.loader import load_fixture
from context_reliability_bench.models.benchmark_case import BenchmarkCase

_FIXTURE = (
    Path(__file__).parent.parent.parent.parent
    / "fixtures"
    / "v1"
    / "distractor.json"
)


class DistractorCategory(BenchmarkCategory):
    @property
    def name(self) -> str:
        return "distractor"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def description(self) -> str:
        return (
            "Tests retrieval quality when context is dominated by topically "
            "adjacent but off-target distractor documents."
        )

    def load_cases(self) -> list[BenchmarkCase]:
        return load_fixture(_FIXTURE)
