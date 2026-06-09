from __future__ import annotations

from typing import Protocol, runtime_checkable

from context_reliability_bench.models.retrieved_context import RetrievedContext


@runtime_checkable
class Metric(Protocol):
    @property
    def name(self) -> str: ...

    def compute(
        self,
        retrieved: tuple[RetrievedContext, ...],
        relevant_ids: frozenset[str],
    ) -> float: ...
