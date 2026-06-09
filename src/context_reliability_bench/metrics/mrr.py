from __future__ import annotations

from context_reliability_bench.models.retrieved_context import RetrievedContext


class ReciprocalRank:
    """Computes reciprocal rank for a single case; average over cases gives MRR."""

    @property
    def name(self) -> str:
        return "reciprocal_rank"

    def compute(
        self,
        retrieved: tuple[RetrievedContext, ...],
        relevant_ids: frozenset[str],
    ) -> float:
        for rc in sorted(retrieved, key=lambda r: r.rank):
            if rc.document.id in relevant_ids:
                return 1.0 / rc.rank
        return 0.0
