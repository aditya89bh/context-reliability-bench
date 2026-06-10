from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.retrieval.protocol import RetrieverAdapter
from context_reliability_bench.runner import run_benchmark


def _empty_frozenset() -> frozenset[str]:
    return frozenset()


@dataclass(frozen=True)
class RetrievalQuery:
    id: str
    query_text: str
    relevant_doc_ids: frozenset[str] = field(default_factory=_empty_frozenset)
    expected_answer: str = "N/A"


def run_retriever_benchmark(
    retriever: RetrieverAdapter,
    queries: Sequence[RetrievalQuery],
    metrics: Sequence[Metric],
    top_k: int = 10,
) -> RunResult:
    if not queries:
        raise ValueError("queries must not be empty")
    if not metrics:
        raise ValueError("metrics must not be empty")

    cases: list[BenchmarkCase] = []
    for q in queries:
        query = Query(id=q.id, text=q.query_text)
        retrieved = retriever.retrieve(query, top_k=top_k)
        if not retrieved:
            continue
        case = BenchmarkCase(
            id=q.id,
            query=query,
            context=tuple(retrieved),
            relevant_doc_ids=q.relevant_doc_ids,
            expected_answer=q.expected_answer,
        )
        cases.append(case)

    if not cases:
        raise ValueError("Retriever returned no results for any query")

    return run_benchmark(cases, metrics, run_id=retriever.name)
