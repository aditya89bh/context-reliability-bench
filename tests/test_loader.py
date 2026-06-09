from __future__ import annotations

from pathlib import Path

import pytest

from context_reliability_bench.loader import FixtureError, load_fixture

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SAMPLE_FIXTURE = FIXTURES_DIR / "sample.json"


def test_load_sample_returns_two_cases() -> None:
    cases = load_fixture(SAMPLE_FIXTURE)
    assert len(cases) == 2


def test_load_sample_first_case_id() -> None:
    cases = load_fixture(SAMPLE_FIXTURE)
    assert cases[0].id == "case-001"


def test_load_sample_first_query() -> None:
    cases = load_fixture(SAMPLE_FIXTURE)
    assert cases[0].query.id == "q-001"
    assert cases[0].query.text == "What is the capital of France?"


def test_load_sample_first_expected_answer() -> None:
    cases = load_fixture(SAMPLE_FIXTURE)
    assert cases[0].expected_answer == "Paris"


def test_load_sample_first_context_count() -> None:
    cases = load_fixture(SAMPLE_FIXTURE)
    assert len(cases[0].context) == 2


def test_load_sample_first_context_ranks() -> None:
    cases = load_fixture(SAMPLE_FIXTURE)
    ranks = [rc.rank for rc in cases[0].context]
    assert ranks == [1, 2]


def test_load_sample_first_context_scores() -> None:
    cases = load_fixture(SAMPLE_FIXTURE)
    assert cases[0].context[0].score == pytest.approx(0.95)
    assert cases[0].context[1].score == pytest.approx(0.80)


def test_load_sample_document_metadata() -> None:
    cases = load_fixture(SAMPLE_FIXTURE)
    assert cases[0].context[0].document.metadata == {"source": "geography-101"}


def test_load_sample_second_case() -> None:
    cases = load_fixture(SAMPLE_FIXTURE)
    assert cases[1].id == "case-002"
    assert cases[1].expected_answer == "William Shakespeare"
    assert len(cases[1].context) == 1


def test_load_nonexistent_file() -> None:
    with pytest.raises(FixtureError, match="Cannot read fixture file"):
        load_fixture(Path("/nonexistent/path/fixture.json"))


def test_load_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not json {", encoding="utf-8")
    with pytest.raises(FixtureError, match="Invalid JSON"):
        load_fixture(bad)


def test_load_missing_cases_key(tmp_path: Path) -> None:
    f = tmp_path / "f.json"
    f.write_text('{"data": []}', encoding="utf-8")
    with pytest.raises(FixtureError, match="'cases' key"):
        load_fixture(f)


def test_load_cases_not_array(tmp_path: Path) -> None:
    f = tmp_path / "f.json"
    f.write_text('{"cases": "oops"}', encoding="utf-8")
    with pytest.raises(FixtureError, match="JSON array"):
        load_fixture(f)


def test_load_case_missing_id(tmp_path: Path) -> None:
    payload = (
        '{"cases": [{"query": {"id": "q1", "text": "q"}, '
        '"context": [{"document": {"id": "d1", "content": "c"}, '
        '"score": 0.9, "rank": 1}], "expected_answer": "a"}]}'
    )
    f = tmp_path / "f.json"
    f.write_text(payload, encoding="utf-8")
    with pytest.raises(FixtureError, match="id"):
        load_fixture(f)


def test_load_case_missing_context(tmp_path: Path) -> None:
    payload = (
        '{"cases": [{"id": "c1", "query": {"id": "q1", "text": "q"}, '
        '"expected_answer": "a"}]}'
    )
    f = tmp_path / "f.json"
    f.write_text(payload, encoding="utf-8")
    with pytest.raises(FixtureError, match="context"):
        load_fixture(f)


def test_load_document_missing_content(tmp_path: Path) -> None:
    payload = (
        '{"cases": [{"id": "c1", "query": {"id": "q1", "text": "q"}, '
        '"context": [{"document": {"id": "d1"}, "score": 0.9, "rank": 1}], '
        '"expected_answer": "a"}]}'
    )
    f = tmp_path / "f.json"
    f.write_text(payload, encoding="utf-8")
    with pytest.raises(FixtureError, match="content"):
        load_fixture(f)
