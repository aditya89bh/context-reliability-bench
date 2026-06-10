from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.reports.dashboard_export import export_dashboard_json
from context_reliability_bench.suite import SuiteResult


def _run(means: list[float], run_id: str = "cat") -> RunResult:
    mrs = tuple(
        MetricResult(
            metric_name=f"m{i}",
            case_scores=(("c0", m), ("c1", m)),
            mean=m,
        )
        for i, m in enumerate(means)
    )
    return RunResult(run_id=run_id, metric_results=mrs)


def _suite() -> SuiteResult:
    r1 = _run([0.8, 0.6], run_id="cat1")
    r2 = _run([0.4], run_id="cat2")
    return SuiteResult(category_results=(("cat1", r1), ("cat2", r2)))


def test_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    assert out.exists()


def test_schema_version(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"


def test_has_categories(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "categories" in data
    assert set(data["categories"].keys()) == {"cat1", "cat2"}


def test_category_has_aggregate_score(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "aggregate_score" in data["categories"]["cat1"]
    assert isinstance(data["categories"]["cat1"]["aggregate_score"], float)


def test_category_has_metrics(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "metrics" in data["categories"]["cat1"]
    assert "m0" in data["categories"]["cat1"]["metrics"]


def test_metric_has_statistics(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    m = data["categories"]["cat1"]["metrics"]["m0"]
    for key in ("mean", "minimum", "maximum", "median", "std_dev"):
        assert key in m


def test_metric_has_case_scores(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    case_scores = data["categories"]["cat1"]["metrics"]["m0"]["case_scores"]
    assert isinstance(case_scores, list)
    assert len(case_scores) == 2


def test_metadata_passed_through(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(
        _suite(), out, run_metadata={"team": "research", "env": "prod"}
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["metadata"]["team"] == "research"
    assert data["metadata"]["env"] == "prod"


def test_default_metadata_is_empty_dict(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["metadata"] == {}


def test_summary_total_categories(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["summary"]["total_categories"] == 2


def test_summary_total_cases(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    # cat1 has 2 cases, cat2 has 2 cases → 4
    assert data["summary"]["total_cases"] == 4


def test_aggregate_score_value(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.json"
    export_dashboard_json(_suite(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    # cat2: single metric with mean 0.4 → aggregate = 0.4
    assert data["categories"]["cat2"]["aggregate_score"] == pytest.approx(0.4)
