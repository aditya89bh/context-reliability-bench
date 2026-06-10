from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext

_K1: float = 1.5
_B: float = 0.75


class BM25RetrieverAdapter:
    """Pure-Python BM25 retriever with no external dependencies."""

    def __init__(self) -> None:
        self._documents: list[Document] = []
        self._doc_term_freqs: list[dict[str, int]] = []
        self._df: dict[str, int] = {}
        self._avgdl: float = 0.0

    @property
    def name(self) -> str:
        return "bm25"

    def index(self, documents: Sequence[Document]) -> None:
        self._documents = list(documents)
        self._doc_term_freqs = []
        self._df = {}

        if not self._documents:
            self._avgdl = 0.0
            return

        total_len = 0
        for doc in self._documents:
            tokens = doc.content.lower().split()
            tf: dict[str, int] = dict(Counter(tokens))
            self._doc_term_freqs.append(tf)
            total_len += len(tokens)
            for term in tf:
                self._df[term] = self._df.get(term, 0) + 1

        self._avgdl = total_len / len(self._documents)

    def retrieve(self, query: Query, top_k: int = 10) -> list[RetrievedContext]:
        if not self._documents:
            return []

        query_terms = query.text.lower().split()
        if not query_terms:
            return []

        n = len(self._documents)
        scores: list[float] = []

        for i in range(n):
            tf_map = self._doc_term_freqs[i]
            dl = sum(tf_map.values())
            score = 0.0
            for term in query_terms:
                tf = tf_map.get(term, 0)
                if tf == 0:
                    continue
                df = self._df.get(term, 0)
                idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
                denom = tf + _K1 * (
                    1 - _B + _B * dl / max(self._avgdl, 1.0)
                )
                tf_norm = tf * (_K1 + 1) / denom
                score += idf * tf_norm
            scores.append(score)

        max_score = max(scores) if scores else 0.0
        if max_score <= 0.0:
            return []

        norm = [s / max_score for s in scores]
        ranked = sorted(enumerate(norm), key=lambda x: x[1], reverse=True)

        results: list[RetrievedContext] = []
        for rank, (doc_idx, score) in enumerate(ranked[:top_k], start=1):
            if score > 0.0:
                results.append(
                    RetrievedContext(
                        document=self._documents[doc_idx],
                        score=score,
                        rank=rank,
                    )
                )
        return results
