from __future__ import annotations

from context_reliability_bench.models.retrieved_context import RetrievedContext


class RecallAtK:
    def __init__(self, k: int) -> None:
        if k <= 0:
            raise ValueError(f"k must be positive, got {k}")
        self._k = k

    @property
    def name(self) -> str:
        return f"recall@{self._k}"

    def compute(
        self,
        retrieved: tuple[RetrievedContext, ...],
        relevant_ids: frozenset[str],
    ) -> float:
        if not relevant_ids:
            return 0.0
        top_k = sorted(retrieved, key=lambda r: r.rank)[: self._k]
        hits = sum(1 for rc in top_k if rc.document.id in relevant_ids)
        return hits / len(relevant_ids)
