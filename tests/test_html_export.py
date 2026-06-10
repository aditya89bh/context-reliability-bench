from __future__ import annotations

from pathlib import Path

from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext
from context_reliability_bench.reports.html_export import export_html
from context_reliability_bench.runner import run_benchmark


def _case() -> BenchmarkCase:
    doc = Document(id="d1", content="Content.", metadata={"src": "test"})
    rc = RetrievedContext(document=doc, score=0.9, rank=1)
    return BenchmarkCase(
        id="c1",
        query=Query(id="q1", text="Question?"),
        context=(rc,),
        relevant_doc_ids=frozenset({"d1"}),
        expected_answer="answer",
    )


def _result(run_id: str = "test-run") -> object:
    from context_reliability_bench.metrics.protocol import Metric

    metrics: list[Metric] = [PrecisionAtK(k=1), RecallAtK(k=1)]
    return run_benchmark([_case()], metrics, run_id=run_id)


def test_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    export_html(_result(), out)  # type: ignore[arg-type]
    assert out.exists()


def test_contains_doctype(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    export_html(_result(), out)  # type: ignore[arg-type]
    assert "<!DOCTYPE html>" in out.read_text(encoding="utf-8")


def test_contains_run_id(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    export_html(_result(run_id="my-run-99"), out)  # type: ignore[arg-type]
    assert "my-run-99" in out.read_text(encoding="utf-8")


def test_contains_metric_name(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    export_html(_result(), out)  # type: ignore[arg-type]
    content = out.read_text(encoding="utf-8")
    assert "precision@1" in content


def test_contains_case_id(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    export_html(_result(), out)  # type: ignore[arg-type]
    assert "c1" in out.read_text(encoding="utf-8")


def test_escapes_html_special_chars(tmp_path: Path) -> None:
    doc = Document(id="d<1>", content="Content.", metadata={})
    rc = RetrievedContext(document=doc, score=0.9, rank=1)
    case = BenchmarkCase(
        id="c<1>",
        query=Query(id="q1", text="Q?"),
        context=(rc,),
        relevant_doc_ids=frozenset({"d<1>"}),
        expected_answer="ans",
    )
    from context_reliability_bench.metrics.protocol import Metric

    metrics: list[Metric] = [PrecisionAtK(k=1)]
    result = run_benchmark([case], metrics, run_id="run<&>")
    out = tmp_path / "report.html"
    export_html(result, out)
    content = out.read_text(encoding="utf-8")
    assert "&lt;" in content
    assert "&amp;" in content


def test_contains_style_tag(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    export_html(_result(), out)  # type: ignore[arg-type]
    assert "<style>" in out.read_text(encoding="utf-8")
