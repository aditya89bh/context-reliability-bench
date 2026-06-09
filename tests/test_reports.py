from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext
from context_reliability_bench.reports.csv_export import export_csv
from context_reliability_bench.reports.json_export import export_json
from context_reliability_bench.runner import run_benchmark


def _simple_case() -> BenchmarkCase:
    doc = Document(id="d1", content="Content.")
    rc = RetrievedContext(document=doc, score=0.9, rank=1)
    return BenchmarkCase(
        id="c1",
        query=Query(id="q1", text="Question?"),
        context=(rc,),
        relevant_doc_ids=frozenset({"d1"}),
        expected_answer="answer",
    )


def _run_result(run_id: str = "test-run") -> object:
    case = _simple_case()
    return run_benchmark([case], [PrecisionAtK(k=1)], run_id=run_id)


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------


def test_json_export_creates_file(tmp_path: Path) -> None:
    result = run_benchmark([_simple_case()], [PrecisionAtK(k=1)])
    out = tmp_path / "report.json"
    export_json(result, out)
    assert out.exists()


def test_json_export_run_id(tmp_path: Path) -> None:
    result = run_benchmark([_simple_case()], [PrecisionAtK(k=1)], run_id="r1")
    out = tmp_path / "report.json"
    export_json(result, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["run_id"] == "r1"


def test_json_export_metric_key(tmp_path: Path) -> None:
    result = run_benchmark([_simple_case()], [PrecisionAtK(k=1)])
    out = tmp_path / "report.json"
    export_json(result, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "precision@1" in data["metrics"]


def test_json_export_mean(tmp_path: Path) -> None:
    result = run_benchmark([_simple_case()], [PrecisionAtK(k=1)])
    out = tmp_path / "report.json"
    export_json(result, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["metrics"]["precision@1"]["mean"] == pytest.approx(1.0)


def test_json_export_case_scores(tmp_path: Path) -> None:
    result = run_benchmark([_simple_case()], [PrecisionAtK(k=1)])
    out = tmp_path / "report.json"
    export_json(result, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    scores = data["metrics"]["precision@1"]["case_scores"]
    assert len(scores) == 1
    assert scores[0]["case_id"] == "c1"
    assert scores[0]["score"] == pytest.approx(1.0)


def test_json_export_multiple_metrics(tmp_path: Path) -> None:
    result = run_benchmark(
        [_simple_case()],
        [PrecisionAtK(k=1), RecallAtK(k=1)],
    )
    out = tmp_path / "report.json"
    export_json(result, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "precision@1" in data["metrics"]
    assert "recall@1" in data["metrics"]


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


def test_csv_export_creates_file(tmp_path: Path) -> None:
    result = run_benchmark([_simple_case()], [PrecisionAtK(k=1)])
    out = tmp_path / "report.csv"
    export_csv(result, out)
    assert out.exists()


def test_csv_export_header(tmp_path: Path) -> None:
    result = run_benchmark([_simple_case()], [PrecisionAtK(k=1)])
    out = tmp_path / "report.csv"
    export_csv(result, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "run_id,metric,case_id,score"


def test_csv_export_row_count(tmp_path: Path) -> None:
    result = run_benchmark(
        [_simple_case()],
        [PrecisionAtK(k=1), RecallAtK(k=1)],
        run_id="r1",
    )
    out = tmp_path / "report.csv"
    export_csv(result, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3  # header + 2 metric rows


def test_csv_export_run_id_in_rows(tmp_path: Path) -> None:
    result = run_benchmark([_simple_case()], [PrecisionAtK(k=1)], run_id="my-run")
    out = tmp_path / "report.csv"
    export_csv(result, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[1].startswith("my-run,")


def test_csv_export_metric_name_in_rows(tmp_path: Path) -> None:
    result = run_benchmark([_simple_case()], [RecallAtK(k=2)])
    out = tmp_path / "report.csv"
    export_csv(result, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert "recall@2" in lines[1]
