from __future__ import annotations

import pytest

from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.retrieval.bm25 import BM25RetrieverAdapter
from context_reliability_bench.retrieval.harness import (
    RetrievalQuery,
    run_retriever_benchmark,
)
from context_reliability_bench.retrieval.in_memory import InMemoryRetrieverAdapter
from context_reliability_bench.retrieval.protocol import RetrieverAdapter
from context_reliability_bench.retrieval.vector import (
    VectorBackend,
    VectorRetrieverAdapter,
)

# ─── fixtures ────────────────────────────────────────────────────────────────


def _docs() -> list[Document]:
    return [
        Document(id="d1", content="the cat sat on the mat"),
        Document(id="d2", content="the dog lay on the rug"),
        Document(id="d3", content="cats and dogs are common pets"),
    ]


def _query(text: str = "cat") -> Query:
    return Query(id="q1", text=text)


# ─── InMemoryRetrieverAdapter ─────────────────────────────────────────────────


def test_in_memory_satisfies_protocol() -> None:
    adapter = InMemoryRetrieverAdapter()
    assert isinstance(adapter, RetrieverAdapter)


def test_in_memory_name() -> None:
    assert InMemoryRetrieverAdapter().name == "in_memory"


def test_in_memory_returns_results() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(_query("cat"), top_k=3)
    assert len(results) >= 1


def test_in_memory_most_relevant_first() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(_query("cat"), top_k=3)
    # d1 contains "cat" twice; d3 contains "cats" (which won't match "cat")
    assert results[0].document.id == "d1"


def test_in_memory_scores_in_range() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(_query("cat mat"), top_k=3)
    for rc in results:
        assert 0.0 <= rc.score <= 1.0


def test_in_memory_top_k_limit() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(_query("the"), top_k=2)
    assert len(results) <= 2


def test_in_memory_empty_index_returns_empty() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index([])
    assert adapter.retrieve(_query("cat")) == []


def test_in_memory_no_match_returns_empty() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(Query(id="q", text="zzznomatch"))
    assert results == []


def test_in_memory_rank_starts_at_one() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(_query("dog"), top_k=2)
    assert results[0].rank == 1


# ─── BM25RetrieverAdapter ─────────────────────────────────────────────────────


def test_bm25_satisfies_protocol() -> None:
    assert isinstance(BM25RetrieverAdapter(), RetrieverAdapter)


def test_bm25_name() -> None:
    assert BM25RetrieverAdapter().name == "bm25"


def test_bm25_returns_results() -> None:
    adapter = BM25RetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(_query("cat"), top_k=3)
    assert len(results) >= 1


def test_bm25_scores_in_range() -> None:
    adapter = BM25RetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(_query("cat"), top_k=3)
    for rc in results:
        assert 0.0 <= rc.score <= 1.0


def test_bm25_top_result_contains_term() -> None:
    adapter = BM25RetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(_query("dog"), top_k=3)
    assert results[0].document.id in {"d2", "d3"}


def test_bm25_top_k_limit() -> None:
    adapter = BM25RetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(_query("the"), top_k=1)
    assert len(results) == 1


def test_bm25_empty_index_returns_empty() -> None:
    adapter = BM25RetrieverAdapter()
    adapter.index([])
    assert adapter.retrieve(_query("cat")) == []


def test_bm25_no_match_returns_empty() -> None:
    adapter = BM25RetrieverAdapter()
    adapter.index(_docs())
    assert adapter.retrieve(Query(id="q", text="zzznomatch")) == []


def test_bm25_rank_starts_at_one() -> None:
    adapter = BM25RetrieverAdapter()
    adapter.index(_docs())
    results = adapter.retrieve(_query("cat"), top_k=2)
    assert results[0].rank == 1


# ─── VectorRetrieverAdapter ──────────────────────────────────────────────────


class _MockBackend:
    """Term-match mock that satisfies VectorBackend."""

    def __init__(self) -> None:
        self._docs: dict[str, str] = {}

    def add(self, doc_id: str, text: str) -> None:
        self._docs[doc_id] = text

    def search(self, query_text: str, top_k: int) -> list[tuple[str, float]]:
        terms = query_text.lower().split()
        scored = []
        for doc_id, text in self._docs.items():
            score = sum(t in text.lower() for t in terms) / max(len(terms), 1)
            scored.append((doc_id, float(score)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


def test_vector_backend_satisfies_protocol() -> None:
    assert isinstance(_MockBackend(), VectorBackend)


def test_vector_adapter_satisfies_protocol() -> None:
    adapter = VectorRetrieverAdapter(_MockBackend())
    assert isinstance(adapter, RetrieverAdapter)


def test_vector_adapter_name_default() -> None:
    assert VectorRetrieverAdapter(_MockBackend()).name == "vector"


def test_vector_adapter_name_custom() -> None:
    assert VectorRetrieverAdapter(_MockBackend(), name="faiss").name == "faiss"


def test_vector_adapter_returns_results() -> None:
    adapter = VectorRetrieverAdapter(_MockBackend())
    adapter.index(_docs())
    results = adapter.retrieve(_query("cat"), top_k=3)
    assert len(results) >= 1


def test_vector_adapter_scores_clamped() -> None:
    adapter = VectorRetrieverAdapter(_MockBackend())
    adapter.index(_docs())
    results = adapter.retrieve(_query("cat"), top_k=3)
    for rc in results:
        assert 0.0 <= rc.score <= 1.0


def test_vector_adapter_unknown_doc_id_skipped() -> None:
    class _BadBackend:
        def add(self, doc_id: str, text: str) -> None:
            pass

        def search(self, query_text: str, top_k: int) -> list[tuple[str, float]]:
            return [("nonexistent_id", 0.9)]

    adapter = VectorRetrieverAdapter(_BadBackend())
    adapter.index(_docs())
    assert adapter.retrieve(_query("cat")) == []


# ─── run_retriever_benchmark ──────────────────────────────────────────────────


def _rq(qid: str, text: str, relevant: set[str]) -> RetrievalQuery:
    return RetrievalQuery(
        id=qid,
        query_text=text,
        relevant_doc_ids=frozenset(relevant),
    )


def test_harness_returns_run_result() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index(_docs())
    queries = [_rq("q1", "cat", {"d1"}), _rq("q2", "dog", {"d2"})]
    metrics_list: list[Metric] = [PrecisionAtK(k=3), RecallAtK(k=3)]
    result = run_retriever_benchmark(adapter, queries, metrics_list)
    assert result.run_id == "in_memory"
    assert len(result.metric_results) == 2


def test_harness_run_id_matches_adapter_name() -> None:
    adapter = BM25RetrieverAdapter()
    adapter.index(_docs())
    queries = [_rq("q1", "cat", {"d1"})]
    result = run_retriever_benchmark(adapter, queries, [PrecisionAtK(k=1)])
    assert result.run_id == "bm25"


def test_harness_empty_queries_raises() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index(_docs())
    with pytest.raises(ValueError, match="queries"):
        run_retriever_benchmark(adapter, [], [PrecisionAtK(k=1)])


def test_harness_empty_metrics_raises() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index(_docs())
    with pytest.raises(ValueError, match="metrics"):
        run_retriever_benchmark(adapter, [_rq("q1", "cat", {"d1"})], [])


def test_harness_no_results_raises() -> None:
    adapter = InMemoryRetrieverAdapter()
    adapter.index(_docs())
    queries = [_rq("q1", "zzznomatch", {"d1"})]
    with pytest.raises(ValueError, match="no results"):
        run_retriever_benchmark(adapter, queries, [PrecisionAtK(k=1)])


def test_retrieval_query_default_fields() -> None:
    q = RetrievalQuery(id="q1", query_text="hello")
    assert q.relevant_doc_ids == frozenset()
    assert q.expected_answer == "N/A"
