from __future__ import annotations

from dataclasses import dataclass

from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    query: Query
    context: tuple[RetrievedContext, ...]
    relevant_doc_ids: frozenset[str]
    expected_answer: str
