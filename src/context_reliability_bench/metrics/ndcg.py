from __future__ import annotations

import math

from context_reliability_bench.models.retrieved_context import RetrievedContext


class NdcgAtK:
    """Normalized Discounted Cumulative Gain at K with binary relevance."""

    def __init__(self, k: int) -> None:
        if k <= 0:
            raise ValueError(f"k must be positive, got {k}")
        self._k = k

    @property
    def name(self) -> str:
        return f"ndcg@{self._k}"

    def compute(
        self,
        retrieved: tuple[RetrievedContext, ...],
        relevant_ids: frozenset[str],
    ) -> float:
        top_k = sorted(retrieved, key=lambda r: r.rank)[: self._k]
        dcg = sum(
            1.0 / math.log2(rc.rank + 1)
            for rc in top_k
            if rc.document.id in relevant_ids
        )
        n_relevant = min(len(relevant_ids), self._k)
        idcg = sum(1.0 / math.log2(i + 2) for i in range(n_relevant))
        return dcg / idcg if idcg > 0.0 else 0.0
