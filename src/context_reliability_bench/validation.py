from __future__ import annotations

from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.retrieved_context import RetrievedContext


class ValidationError(Exception):
    pass


def validate_benchmark_case(case: BenchmarkCase) -> None:
    if not case.id:
        raise ValidationError("BenchmarkCase.id must not be empty")
    if not case.query.id:
        raise ValidationError("Query.id must not be empty")
    if not case.query.text:
        raise ValidationError("Query.text must not be empty")
    if not case.expected_answer:
        raise ValidationError(
            "BenchmarkCase.expected_answer must not be empty"
        )
    if not case.context:
        raise ValidationError("BenchmarkCase.context must not be empty")
    _validate_context_ranks(case.context)
    for rc in case.context:
        _validate_retrieved_context(rc)
    if not case.relevant_doc_ids:
        raise ValidationError(
            "BenchmarkCase.relevant_doc_ids must not be empty"
        )
    context_doc_ids = frozenset(rc.document.id for rc in case.context)
    unknown = case.relevant_doc_ids - context_doc_ids
    if unknown:
        ids = ", ".join(sorted(unknown))
        raise ValidationError(
            f"relevant_doc_ids contains IDs not in context: {ids}"
        )


def _validate_context_ranks(
    context: tuple[RetrievedContext, ...],
) -> None:
    ranks = sorted(rc.rank for rc in context)
    if ranks != list(range(1, len(context) + 1)):
        raise ValidationError(
            "RetrievedContext ranks must be consecutive starting from 1"
        )


def _validate_retrieved_context(rc: RetrievedContext) -> None:
    if not rc.document.id:
        raise ValidationError("Document.id must not be empty")
    if not rc.document.content:
        raise ValidationError("Document.content must not be empty")
    if not 0.0 <= rc.score <= 1.0:
        raise ValidationError(
            f"RetrievedContext.score must be in [0.0, 1.0], got {rc.score}"
        )
