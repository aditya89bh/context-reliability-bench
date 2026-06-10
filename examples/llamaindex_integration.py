"""
LlamaIndex integration example.

Run with:
    python examples/llamaindex_integration.py

Demonstrates how to wrap a LlamaIndex retriever as a RetrieverAdapter so it
can be benchmarked directly with context-reliability-bench.

This example uses a self-contained mock that runs without LlamaIndex installed.
To use a real LlamaIndex retriever, see the comments marked  # LLAMAINDEX:
"""

from __future__ import annotations

import sys
from pathlib import Path

from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext
from context_reliability_bench.retrieval import (
    RetrievalQuery,
    RetrieverAdapter,
    run_retriever_benchmark,
)

_ROOT = Path(__file__).parent.parent

# ── Mock LlamaIndex node/retriever types ──────────────────────────────────────


class _MockNodeWithScore:
    """Mimics llama_index.core.schema.NodeWithScore."""

    def __init__(self, node_id: str, text: str, score: float) -> None:
        self.node_id = node_id
        self.text = text
        self.score = score


class _MockLlamaRetriever:
    """
    Mimics a llama_index BaseRetriever.

    Replace with a real LlamaIndex retriever, e.g.:

        # LLAMAINDEX: from llama_index.core import (
        #     VectorStoreIndex, SimpleDirectoryReader
        # )
        # LLAMAINDEX: docs = SimpleDirectoryReader("data/").load_data()
        # LLAMAINDEX: index = VectorStoreIndex.from_documents(docs)
        # LLAMAINDEX: retriever = index.as_retriever(similarity_top_k=5)
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def add(self, node_id: str, text: str) -> None:
        self._store[node_id] = text

    def retrieve(self, query: str) -> list[_MockNodeWithScore]:
        terms = query.lower().split()
        scored: list[_MockNodeWithScore] = []
        for node_id, text in self._store.items():
            hits = sum(t in text.lower() for t in terms)
            score = hits / max(len(terms), 1)
            if score > 0:
                scored.append(_MockNodeWithScore(node_id, text, score))
        scored.sort(key=lambda n: n.score, reverse=True)
        max_score = scored[0].score if scored else 1.0
        for n in scored:
            n.score = n.score / max_score
        return scored


# ── LlamaIndexRetrieverAdapter ────────────────────────────────────────────────


class LlamaIndexRetrieverAdapter:
    """
    RetrieverAdapter wrapping a LlamaIndex retriever.

    The adapter implements the RetrieverAdapter protocol directly (no VectorBackend
    indirection) because LlamaIndex retrievers already produce ranked results.

    Usage with a real LlamaIndex retriever:

        # LLAMAINDEX: retriever = index.as_retriever(similarity_top_k=top_k)
        # LLAMAINDEX: adapter = LlamaIndexRetrieverAdapter(retriever, corpus_map)
        # LLAMAINDEX: # where corpus_map: dict[node_id, Document]
    """

    def __init__(
        self,
        llama_retriever: _MockLlamaRetriever,
        top_k: int = 5,
    ) -> None:
        self._retriever = llama_retriever
        self._top_k = top_k
        self._doc_map: dict[str, Document] = {}

    @property
    def name(self) -> str:
        return "llamaindex"

    def index(self, documents: list[Document]) -> None:
        self._doc_map = {}
        for doc in documents:
            self._retriever.add(doc.id, doc.content)
            self._doc_map[doc.id] = doc

    def retrieve(self, query: Query, top_k: int = 10) -> list[RetrievedContext]:
        nodes = self._retriever.retrieve(query.text)
        results: list[RetrievedContext] = []
        for rank, node in enumerate(nodes[:top_k], start=1):
            doc = self._doc_map.get(node.node_id)
            if doc is None:
                continue
            results.append(
                RetrievedContext(
                    document=doc,
                    score=max(0.0, min(1.0, node.score)),
                    rank=rank,
                )
            )
        return results


# ── runtime_checkable protocol check ─────────────────────────────────────────
assert isinstance(
    LlamaIndexRetrieverAdapter(_MockLlamaRetriever()), RetrieverAdapter
)

# ── Demo corpus and queries ───────────────────────────────────────────────────

_CORPUS = [
    Document(id="d1", content="transformer architecture uses attention mechanisms"),
    Document(id="d2", content="BERT is a bidirectional transformer for NLP tasks"),
    Document(id="d3", content="GPT generates text using autoregressive models"),
    Document(id="d4", content="vector databases store high-dimensional embeddings"),
    Document(id="d5", content="RAG retrieves documents to augment LLM answers"),
]

_QUERIES = [
    RetrievalQuery(
        id="q1",
        query_text="transformer attention BERT",
        relevant_doc_ids=frozenset({"d1", "d2"}),
    ),
    RetrievalQuery(
        id="q2",
        query_text="retrieval augmented generation RAG",
        relevant_doc_ids=frozenset({"d5"}),
    ),
    RetrievalQuery(
        id="q3",
        query_text="language model text generation",
        relevant_doc_ids=frozenset({"d3"}),
    ),
]


def main() -> int:
    print("=== LlamaIndex Integration Example ===\n")
    print(
        "Using mock LlamaIndex-style retriever "
        "(swap in a real retriever to use live data)\n"
    )

    llama_retriever = _MockLlamaRetriever()
    adapter = LlamaIndexRetrieverAdapter(llama_retriever, top_k=5)
    adapter.index(_CORPUS)

    k = 3
    metrics: list[Metric] = [PrecisionAtK(k=k), NdcgAtK(k=k)]
    result = run_retriever_benchmark(adapter, _QUERIES, metrics, top_k=k)

    print(f"Retriever: {result.run_id}")
    for mr in result.metric_results:
        print(f"  {mr.metric_name:<14} mean={mr.mean:.4f}")

    out_dir = _ROOT / "examples" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    from context_reliability_bench.reports import export_json

    export_json(result, out_dir / "llamaindex_result.json")
    print(f"\nResult written to {out_dir}/llamaindex_result.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
