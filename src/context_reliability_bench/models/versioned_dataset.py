from __future__ import annotations

from dataclasses import dataclass

from context_reliability_bench.models.benchmark_case import BenchmarkCase


@dataclass(frozen=True)
class VersionedDataset:
    format_version: str
    category: str
    cases: tuple[BenchmarkCase, ...]

    def __len__(self) -> int:
        return len(self.cases)
