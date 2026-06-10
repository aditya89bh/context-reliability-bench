from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.reports.comparison_export import (
    MetricDelta,
    compare_runs,
    export_comparison_json,
    export_comparison_markdown,
)


def _run(
    metrics: dict[str, float],
    run_id: str = "run",
) -> RunResult:
    mrs = tuple(
        MetricResult(
            metric_name=name,
            case_scores=(("c1", mean),),
            mean=mean,
        )
        for name, mean in metrics.items()
    )
    return RunResult(run_id=run_id, metric_results=mrs)


def _baseline() -> RunResult:
    return _run({"precision@1": 0.4, "recall@1": 0.25}, run_id="baseline")


def _candidate() -> RunResult:
    return _run({"precision@1": 0.8, "recall@1": 0.5}, run_id="candidate")


def test_compare_runs_returns_tuple() -> None:
    deltas = compare_runs(_baseline(), _candidate())
    assert isinstance(deltas, tuple)


def test_compare_runs_metric_count() -> None:
    deltas = compare_runs(_baseline(), _candidate())
    assert len(deltas) == 2


def test_compare_runs_delta_value() -> None:
    deltas = compare_runs(_baseline(), _candidate())
    delta_map = {d.metric_name: d for d in deltas}
    assert delta_map["precision@1"].delta == pytest.approx(0.4)


def test_compare_runs_improved_true_when_positive() -> None:
    deltas = compare_runs(_baseline(), _candidate())
    for d in deltas:
        assert d.improved is True


def test_compare_runs_improved_false_when_negative() -> None:
    b = _run({"p@1": 0.9})
    c = _run({"p@1": 0.5})
    deltas = compare_runs(b, c)
    assert deltas[0].improved is False


def test_compare_runs_delta_is_candidate_minus_baseline() -> None:
    b = _run({"p@1": 0.3})
    c = _run({"p@1": 0.7})
    deltas = compare_runs(b, c)
    assert deltas[0].delta == pytest.approx(0.4)
    assert deltas[0].baseline_mean == pytest.approx(0.3)
    assert deltas[0].candidate_mean == pytest.approx(0.7)


def test_compare_runs_metric_only_in_candidate() -> None:
    b = _run({"p@1": 0.5})
    c = _run({"p@1": 0.7, "r@1": 0.6})
    deltas = compare_runs(b, c)
    delta_map = {d.metric_name: d for d in deltas}
    assert "r@1" in delta_map
    assert delta_map["r@1"].baseline_mean == 0.0


def test_json_export_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "comparison.json"
    export_comparison_json(_baseline(), _candidate(), out)
    assert out.exists()


def test_json_export_run_ids(tmp_path: Path) -> None:
    out = tmp_path / "comparison.json"
    export_comparison_json(_baseline(), _candidate(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["baseline_run_id"] == "baseline"
    assert data["candidate_run_id"] == "candidate"


def test_json_export_metrics_list(tmp_path: Path) -> None:
    out = tmp_path / "comparison.json"
    export_comparison_json(_baseline(), _candidate(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["metrics"]) == 2


def test_markdown_export_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "comparison.md"
    export_comparison_markdown(_baseline(), _candidate(), out)
    assert out.exists()


def test_markdown_export_contains_header(tmp_path: Path) -> None:
    out = tmp_path / "comparison.md"
    export_comparison_markdown(_baseline(), _candidate(), out)
    content = out.read_text(encoding="utf-8")
    assert "# Benchmark Comparison" in content


def test_markdown_export_contains_run_ids(tmp_path: Path) -> None:
    out = tmp_path / "comparison.md"
    export_comparison_markdown(_baseline(), _candidate(), out)
    content = out.read_text(encoding="utf-8")
    assert "baseline" in content
    assert "candidate" in content


def test_metric_delta_is_frozen() -> None:
    import dataclasses

    d = MetricDelta(
        metric_name="p@1",
        baseline_mean=0.3,
        candidate_mean=0.7,
        delta=0.4,
        improved=True,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.delta = 0.0  # type: ignore[misc]
