from __future__ import annotations

import pytest

from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext
from context_reliability_bench.validation import (
    ValidationError,
    validate_benchmark_case,
)


def _doc(
    id: str = "doc-1",
    content: str = "Some content.",
    metadata: dict[str, str] | None = None,
) -> Document:
    return Document(id=id, content=content, metadata=metadata or {})


def _query(id: str = "q-1", text: str = "A question?") -> Query:
    return Query(id=id, text=text)


def _rc(
    doc: Document | None = None,
    score: float = 0.9,
    rank: int = 1,
) -> RetrievedContext:
    return RetrievedContext(document=doc or _doc(), score=score, rank=rank)


def _case(
    id: str = "case-1",
    query: Query | None = None,
    context: tuple[RetrievedContext, ...] | None = None,
    relevant_doc_ids: frozenset[str] | None = None,
    expected_answer: str = "answer",
) -> BenchmarkCase:
    ctx = context if context is not None else (_rc(),)
    rel_ids = (
        relevant_doc_ids
        if relevant_doc_ids is not None
        else frozenset(rc.document.id for rc in ctx)
    )
    return BenchmarkCase(
        id=id,
        query=query or _query(),
        context=ctx,
        relevant_doc_ids=rel_ids,
        expected_answer=expected_answer,
    )


def test_document_default_metadata() -> None:
    doc = Document(id="d1", content="text")
    assert doc.metadata == {}


def test_document_custom_metadata() -> None:
    doc = Document(id="d1", content="text", metadata={"k": "v"})
    assert doc.metadata == {"k": "v"}


def test_query_fields() -> None:
    q = Query(id="q1", text="What?")
    assert q.id == "q1"
    assert q.text == "What?"


def test_retrieved_context_fields() -> None:
    rc = _rc(score=0.75, rank=2)
    assert rc.score == 0.75
    assert rc.rank == 2
    assert rc.document.id == "doc-1"


def test_benchmark_case_fields() -> None:
    case = _case()
    assert case.id == "case-1"
    assert case.expected_answer == "answer"
    assert len(case.context) == 1


def test_validate_case_ok() -> None:
    validate_benchmark_case(_case())


def test_validate_multi_context_ok() -> None:
    context = (_rc(rank=1), _rc(rank=2))
    validate_benchmark_case(_case(context=context))


def test_validate_empty_case_id() -> None:
    with pytest.raises(ValidationError, match="id must not be empty"):
        validate_benchmark_case(_case(id=""))


def test_validate_empty_query_id() -> None:
    with pytest.raises(ValidationError, match="id must not be empty"):
        validate_benchmark_case(_case(query=Query(id="", text="q?")))


def test_validate_empty_query_text() -> None:
    with pytest.raises(ValidationError, match="text must not be empty"):
        validate_benchmark_case(_case(query=Query(id="q1", text="")))


def test_validate_empty_expected_answer() -> None:
    with pytest.raises(ValidationError, match="expected_answer must not be empty"):
        validate_benchmark_case(_case(expected_answer=""))


def test_validate_empty_context() -> None:
    with pytest.raises(ValidationError, match="context must not be empty"):
        validate_benchmark_case(_case(context=()))


def test_validate_non_consecutive_ranks() -> None:
    context = (_rc(rank=1), _rc(rank=3))
    with pytest.raises(ValidationError, match="ranks must be consecutive"):
        validate_benchmark_case(_case(context=context))


def test_validate_duplicate_ranks() -> None:
    context = (_rc(rank=1), _rc(rank=1))
    with pytest.raises(ValidationError, match="ranks must be consecutive"):
        validate_benchmark_case(_case(context=context))


def test_validate_score_above_range() -> None:
    context = (_rc(score=1.1),)
    with pytest.raises(ValidationError, match="score must be in"):
        validate_benchmark_case(_case(context=context))


def test_validate_score_below_range() -> None:
    context = (_rc(score=-0.1),)
    with pytest.raises(ValidationError, match="score must be in"):
        validate_benchmark_case(_case(context=context))


def test_validate_empty_document_id() -> None:
    context = (_rc(doc=_doc(id="")),)
    with pytest.raises(ValidationError, match="Document.id must not be empty"):
        validate_benchmark_case(_case(context=context))


def test_validate_empty_document_content() -> None:
    context = (_rc(doc=_doc(content="")),)
    with pytest.raises(ValidationError, match="content must not be empty"):
        validate_benchmark_case(_case(context=context))


def test_validate_empty_relevant_doc_ids() -> None:
    with pytest.raises(ValidationError, match="relevant_doc_ids must not be empty"):
        validate_benchmark_case(_case(relevant_doc_ids=frozenset()))


def test_validate_unknown_relevant_doc_id() -> None:
    with pytest.raises(ValidationError, match="not in context"):
        validate_benchmark_case(
            _case(relevant_doc_ids=frozenset({"unknown-doc"}))
        )
