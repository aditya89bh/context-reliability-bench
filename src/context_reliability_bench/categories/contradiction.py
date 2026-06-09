from __future__ import annotations

from pathlib import Path

from context_reliability_bench.categories.base import BenchmarkCategory
from context_reliability_bench.loader import load_fixture
from context_reliability_bench.models.benchmark_case import BenchmarkCase

_FIXTURE = (
    Path(__file__).parent.parent.parent.parent
    / "fixtures"
    / "v1"
    / "contradiction.json"
)


class ContradictionCategory(BenchmarkCategory):
    @property
    def name(self) -> str:
        return "contradiction"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def description(self) -> str:
        return (
            "Tests retrieval quality when context contains contradictory "
            "documents, only one of which is factually correct."
        )

    def load_cases(self) -> list[BenchmarkCase]:
        return load_fixture(_FIXTURE)
