from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext


@runtime_checkable
class VectorBackend(Protocol):
    """Abstract interface for vector-database backends.

    Implement this to plug in any embedding model and vector store
    without creating a hard dependency on a specific library.
    """

    def add(self, doc_id: str, text: str) -> None: ...

    def search(
        self, query_text: str, top_k: int
    ) -> list[tuple[str, float]]: ...


class VectorRetrieverAdapter:
    """Retriever that delegates embedding and search to a VectorBackend."""

    def __init__(self, backend: VectorBackend, name: str = "vector") -> None:
        self._backend = backend
        self._name = name
        self._doc_map: dict[str, Document] = {}

    @property
    def name(self) -> str:
        return self._name

    def index(self, documents: Sequence[Document]) -> None:
        self._doc_map = {}
        for doc in documents:
            self._backend.add(doc.id, doc.content)
            self._doc_map[doc.id] = doc

    def retrieve(self, query: Query, top_k: int = 10) -> list[RetrievedContext]:
        raw = self._backend.search(query.text, top_k)
        results: list[RetrievedContext] = []
        for rank, (doc_id, score) in enumerate(raw, start=1):
            doc = self._doc_map.get(doc_id)
            if doc is None:
                continue
            clamped = max(0.0, min(1.0, score))
            results.append(RetrievedContext(document=doc, score=clamped, rank=rank))
        return results
