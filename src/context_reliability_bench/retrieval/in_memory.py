from __future__ import annotations

from collections.abc import Sequence

from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext


class InMemoryRetrieverAdapter:
    """Term-overlap retriever that holds documents in memory."""

    def __init__(self) -> None:
        self._documents: list[Document] = []

    @property
    def name(self) -> str:
        return "in_memory"

    def index(self, documents: Sequence[Document]) -> None:
        self._documents = list(documents)

    def retrieve(self, query: Query, top_k: int = 10) -> list[RetrievedContext]:
        terms = query.text.lower().split()
        if not terms or not self._documents:
            return []

        scored: list[tuple[Document, float]] = [
            (doc, self._score(doc.content.lower(), terms))
            for doc in self._documents
        ]
        scored = [(d, s) for d, s in scored if s > 0.0]
        scored.sort(key=lambda x: x[1], reverse=True)

        if not scored:
            return []

        max_score = scored[0][1]
        results: list[RetrievedContext] = []
        for rank, (doc, score) in enumerate(scored[:top_k], start=1):
            normalized = min(1.0, score / max_score)
            results.append(RetrievedContext(document=doc, score=normalized, rank=rank))
        return results

    @staticmethod
    def _score(content: str, terms: list[str]) -> float:
        return sum(content.count(term) for term in terms) / len(terms)
