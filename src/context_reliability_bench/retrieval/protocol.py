from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext


@runtime_checkable
class RetrieverAdapter(Protocol):
    @property
    def name(self) -> str: ...

    def index(self, documents: Sequence[Document]) -> None: ...

    def retrieve(
        self,
        query: Query,
        top_k: int = 10,
    ) -> list[RetrievedContext]: ...
