"""
LangChain integration example.

Run with:
    python examples/langchain_integration.py

Demonstrates how to wrap a LangChain vector store as a VectorBackend so it
can be benchmarked with context-reliability-bench without any changes to your
retrieval pipeline.

This example uses a self-contained mock that runs without LangChain installed.
To use a real LangChain backend, see the comments marked  # LANGCHAIN:
"""

from __future__ import annotations

import sys
from pathlib import Path

from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.models.document import Document
from context_reliability_bench.retrieval import (
    RetrievalQuery,
    VectorRetrieverAdapter,
    run_retriever_benchmark,
)
from context_reliability_bench.retrieval.vector import VectorBackend

_ROOT = Path(__file__).parent.parent

# ── Mock implementations (replace with real LangChain objects) ─────────────────


class _MockEmbeddings:
    """
    Replace with a real LangChain embedding model, e.g.:
        # LANGCHAIN: from langchain_openai import OpenAIEmbeddings
        # LANGCHAIN: embeddings = OpenAIEmbeddings()
    """

    def embed_query(self, text: str) -> list[float]:
        tokens = sorted(set(text.lower().split()))
        return [float(tokens.count(t)) for t in tokens] if tokens else [0.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]


class _MockVectorStore:
    """
    Replace with a real LangChain vector store, e.g.:
        # LANGCHAIN: from langchain_community.vectorstores import Chroma
        # LANGCHAIN: store = Chroma(embedding_function=OpenAIEmbeddings())
    """

    def __init__(self) -> None:
        self._vectors: list[tuple[str, list[float]]] = []

    def add_texts(
        self, texts: list[str], metadatas: list[dict[str, str]]
    ) -> list[str]:
        embeddings = _MockEmbeddings()
        for text, meta in zip(texts, metadatas, strict=True):
            vec = embeddings.embed_query(text)
            self._vectors.append((meta["doc_id"], vec))
        return [m["doc_id"] for m in metadatas]

    def similarity_search_with_score(
        self, query: str, k: int
    ) -> list[tuple[str, float]]:
        q_vec = _MockEmbeddings().embed_query(query)
        scored: list[tuple[str, float]] = []
        for doc_id, vec in self._vectors:
            score = self._cosine(q_vec, vec)
            scored.append((doc_id, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        length = min(len(a), len(b))
        if length == 0:
            return 0.0
        dot = sum(a[i] * b[i] for i in range(length))
        mag_a = sum(x * x for x in a) ** 0.5
        mag_b = sum(x * x for x in b) ** 0.5
        denom = mag_a * mag_b
        return dot / denom if denom > 0 else 0.0


# ── LangChainVectorBackend adapter ────────────────────────────────────────────


class LangChainVectorBackend:
    """
    VectorBackend that wraps a LangChain-compatible vector store.

    Usage with a real LangChain store:

        # LANGCHAIN: from langchain_openai import OpenAIEmbeddings
        # LANGCHAIN: from langchain_community.vectorstores import Chroma
        # LANGCHAIN: backend = LangChainVectorBackend(
        # LANGCHAIN:     Chroma(embedding_function=OpenAIEmbeddings())
        # LANGCHAIN: )

    The store must support:
        store.add_texts(texts, metadatas=[{"doc_id": id}])
        store.similarity_search_with_score(query_text, k=top_k)
            → list of (doc_id_str, float_score)
    """

    def __init__(self, store: _MockVectorStore) -> None:
        self._store = store

    def add(self, doc_id: str, text: str) -> None:
        self._store.add_texts([text], metadatas=[{"doc_id": doc_id}])

    def search(self, query_text: str, top_k: int) -> list[tuple[str, float]]:
        raw = self._store.similarity_search_with_score(query_text, k=top_k)
        # Clamp cosine similarity to [0, 1]
        return [(doc_id, max(0.0, min(1.0, score))) for doc_id, score in raw]


# ── runtime_checkable protocol check ─────────────────────────────────────────
assert isinstance(LangChainVectorBackend(_MockVectorStore()), VectorBackend)


# ── Demo corpus and queries ───────────────────────────────────────────────────


_CORPUS = [
    Document(id="d1", content="Python is a high-level programming language"),
    Document(id="d2", content="Java is an object-oriented programming language"),
    Document(id="d3", content="SQL is used for relational database queries"),
    Document(id="d4", content="machine learning trains models on data"),
]

_QUERIES = [
    RetrievalQuery(
        id="q1",
        query_text="programming language",
        relevant_doc_ids=frozenset({"d1", "d2"}),
    ),
    RetrievalQuery(
        id="q2",
        query_text="database SQL query",
        relevant_doc_ids=frozenset({"d3"}),
    ),
]


def main() -> int:
    print("=== LangChain Integration Example ===\n")
    print("Using mock LangChain-style store (swap in a real store to use live data)\n")

    backend = LangChainVectorBackend(_MockVectorStore())
    adapter = VectorRetrieverAdapter(backend, name="langchain_mock")
    adapter.index(_CORPUS)

    k = 3
    metrics: list[Metric] = [PrecisionAtK(k=k), RecallAtK(k=k)]
    result = run_retriever_benchmark(adapter, _QUERIES, metrics, top_k=k)

    print(f"Retriever: {result.run_id}")
    for mr in result.metric_results:
        print(f"  {mr.metric_name:<14} mean={mr.mean:.4f}")

    out_dir = _ROOT / "examples" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    from context_reliability_bench.reports import export_json

    export_json(result, out_dir / "langchain_result.json")
    print(f"\nResult written to {out_dir}/langchain_result.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
