from __future__ import annotations

from dataclasses import dataclass

from context_reliability_bench.models.document import Document


@dataclass(frozen=True)
class RetrievedContext:
    document: Document
    score: float
    rank: int
