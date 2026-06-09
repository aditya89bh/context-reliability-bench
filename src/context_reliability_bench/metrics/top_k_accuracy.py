from __future__ import annotations

from context_reliability_bench.models.retrieved_context import RetrievedContext


class TopKAccuracy:
    def __init__(self, k: int) -> None:
        if k <= 0:
            raise ValueError(f"k must be positive, got {k}")
        self._k = k

    @property
    def name(self) -> str:
        return f"top{self._k}_accuracy"

    def compute(
        self,
        retrieved: tuple[RetrievedContext, ...],
        relevant_ids: frozenset[str],
    ) -> float:
        top_k = sorted(retrieved, key=lambda r: r.rank)[: self._k]
        return 1.0 if any(rc.document.id in relevant_ids for rc in top_k) else 0.0
