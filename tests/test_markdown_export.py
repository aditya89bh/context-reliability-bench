from __future__ import annotations

from pathlib import Path

from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext
from context_reliability_bench.reports.markdown_export import export_markdown
from context_reliability_bench.runner import run_benchmark


def _case() -> BenchmarkCase:
    doc = Document(id="d1", content="Content.")
    rc = RetrievedContext(document=doc, score=0.9, rank=1)
    return BenchmarkCase(
        id="c1",
        query=Query(id="q1", text="Q?"),
        context=(rc,),
        relevant_doc_ids=frozenset({"d1"}),
        expected_answer="ans",
    )


def _result(run_id: str = "test-run") -> object:
    metrics: list[Metric] = [PrecisionAtK(k=1), RecallAtK(k=1)]
    return run_benchmark([_case()], metrics, run_id=run_id)


def test_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    export_markdown(_result(), out)  # type: ignore[arg-type]
    assert out.exists()


def test_contains_h1_with_run_id(tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    export_markdown(_result(run_id="my-bench"), out)  # type: ignore[arg-type]
    content = out.read_text(encoding="utf-8")
    assert "# Benchmark Report: my-bench" in content


def test_contains_summary_section(tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    export_markdown(_result(), out)  # type: ignore[arg-type]
    content = out.read_text(encoding="utf-8")
    assert "## Summary" in content


def test_contains_metric_table_header(tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    export_markdown(_result(), out)  # type: ignore[arg-type]
    content = out.read_text(encoding="utf-8")
    assert "| Metric | Mean Score |" in content


def test_contains_metric_name(tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    export_markdown(_result(), out)  # type: ignore[arg-type]
    content = out.read_text(encoding="utf-8")
    assert "precision@1" in content


def test_contains_case_id_in_section(tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    export_markdown(_result(), out)  # type: ignore[arg-type]
    content = out.read_text(encoding="utf-8")
    assert "c1" in content


def test_pipe_in_id_is_escaped(tmp_path: Path) -> None:
    doc = Document(id="d|1", content="c.")
    rc = RetrievedContext(document=doc, score=0.9, rank=1)
    case = BenchmarkCase(
        id="c|1",
        query=Query(id="q1", text="Q?"),
        context=(rc,),
        relevant_doc_ids=frozenset({"d|1"}),
        expected_answer="ans",
    )
    metrics: list[Metric] = [PrecisionAtK(k=1)]
    result = run_benchmark([case], metrics, run_id="run")
    out = tmp_path / "report.md"
    export_markdown(result, out)
    content = out.read_text(encoding="utf-8")
    assert r"c\|1" in content
