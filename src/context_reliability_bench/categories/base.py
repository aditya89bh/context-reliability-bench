from __future__ import annotations

from abc import ABC, abstractmethod

from context_reliability_bench.models.benchmark_case import BenchmarkCase


class BenchmarkCategory(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def load_cases(self) -> list[BenchmarkCase]: ...
