from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext


class FixtureError(Exception):
    pass


def load_fixture(path: Path) -> list[BenchmarkCase]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FixtureError(f"Cannot read fixture file: {path}") from exc
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FixtureError(f"Invalid JSON in fixture file: {path}") from exc
    return _parse_payload(payload)


def _parse_payload(payload: Any) -> list[BenchmarkCase]:
    if not isinstance(payload, dict) or "cases" not in payload:
        raise FixtureError(
            "Fixture must be a JSON object with a 'cases' key"
        )
    cases = payload["cases"]
    if not isinstance(cases, list):
        raise FixtureError("Fixture 'cases' must be a JSON array")
    return [_parse_case(c, i) for i, c in enumerate(cases)]


def _parse_case(raw: Any, index: int) -> BenchmarkCase:
    loc = f"cases[{index}]"
    if not isinstance(raw, dict):
        raise FixtureError(f"{loc} must be a JSON object")
    context_raw = raw.get("context")
    if not isinstance(context_raw, list):
        raise FixtureError(f"{loc}.context must be a JSON array")
    return BenchmarkCase(
        id=_req_str(raw, "id", loc),
        query=_parse_query(raw.get("query"), loc),
        context=tuple(
            _parse_retrieved_context(c, loc, i)
            for i, c in enumerate(context_raw)
        ),
        relevant_doc_ids=frozenset(
            _req_str_list(raw, "relevant_doc_ids", loc)
        ),
        expected_answer=_req_str(raw, "expected_answer", loc),
    )


def _parse_query(raw: Any, parent: str) -> Query:
    loc = f"{parent}.query"
    if not isinstance(raw, dict):
        raise FixtureError(f"{loc} must be a JSON object")
    return Query(
        id=_req_str(raw, "id", loc),
        text=_req_str(raw, "text", loc),
    )


def _parse_retrieved_context(
    raw: Any, parent: str, index: int
) -> RetrievedContext:
    loc = f"{parent}.context[{index}]"
    if not isinstance(raw, dict):
        raise FixtureError(f"{loc} must be a JSON object")
    score = raw.get("score")
    rank = raw.get("rank")
    if not isinstance(score, (int, float)):
        raise FixtureError(f"{loc}.score must be a number")
    if not isinstance(rank, int):
        raise FixtureError(f"{loc}.rank must be an integer")
    return RetrievedContext(
        document=_parse_document(raw.get("document"), loc),
        score=float(score),
        rank=rank,
    )


def _parse_document(raw: Any, parent: str) -> Document:
    loc = f"{parent}.document"
    if not isinstance(raw, dict):
        raise FixtureError(f"{loc} must be a JSON object")
    raw_meta = raw.get("metadata", {})
    if not isinstance(raw_meta, dict):
        raise FixtureError(f"{loc}.metadata must be a JSON object")
    metadata = {str(k): str(v) for k, v in raw_meta.items()}
    return Document(
        id=_req_str(raw, "id", loc),
        content=_req_str(raw, "content", loc),
        metadata=metadata,
    )


def _req_str(raw: Any, key: str, loc: str) -> str:
    value = raw.get(key) if isinstance(raw, dict) else None
    if not isinstance(value, str):
        raise FixtureError(f"{loc}.{key} must be a string")
    return value


def _req_str_list(raw: Any, key: str, loc: str) -> list[str]:
    value = raw.get(key) if isinstance(raw, dict) else None
    if not isinstance(value, list):
        raise FixtureError(f"{loc}.{key} must be a JSON array")
    result: list[str] = []
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise FixtureError(f"{loc}.{key}[{i}] must be a string")
        result.append(item)
    return result
