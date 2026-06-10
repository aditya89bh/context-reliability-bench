from __future__ import annotations

import pytest

from context_reliability_bench.comparison_engine import (
    BenchmarkComparisonEngine,
    ComparisonError,
    ComparisonResult,
    MetricComparison,
)
from context_reliability_bench.history import BenchmarkHistory, BenchmarkRunRecord
from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult


def _run(means: dict[str, float], run_id: str = "r") -> RunResult:
    return RunResult(
        run_id=run_id,
        metric_results=tuple(
            MetricResult(
                metric_name=name,
                case_scores=(("c0", m),),
                mean=m,
            )
            for name, m in means.items()
        ),
    )


def _rec(
    run_id: str,
    timestamp: str,
    config_id: str = "cfg",
    means: dict[str, float] | None = None,
) -> BenchmarkRunRecord:
    return BenchmarkRunRecord(
        run_result=_run(means or {"p@5": 0.5}, run_id=run_id),
        timestamp=timestamp,
        config_id=config_id,
    )


_engine = BenchmarkComparisonEngine()


def test_compare_returns_comparison_result() -> None:
    base = _run({"p@5": 0.5})
    cand = _run({"p@5": 0.7})
    result = _engine.compare(base, cand)
    assert isinstance(result, ComparisonResult)


def test_compare_delta_positive_when_improved() -> None:
    base = _run({"p@5": 0.5})
    cand = _run({"p@5": 0.8})
    result = _engine.compare(base, cand)
    assert result.metric_comparisons[0].delta == pytest.approx(0.3)


def test_compare_delta_negative_when_regressed() -> None:
    base = _run({"p@5": 0.8})
    cand = _run({"p@5": 0.6})
    result = _engine.compare(base, cand)
    assert result.metric_comparisons[0].delta == pytest.approx(-0.2)


def test_compare_improved_metrics_tuple() -> None:
    base = _run({"p@5": 0.5, "r@5": 0.4})
    cand = _run({"p@5": 0.7, "r@5": 0.3})
    result = _engine.compare(base, cand)
    assert "p@5" in result.improved_metrics
    assert "r@5" in result.regressed_metrics


def test_compare_overall_change_mean_of_deltas() -> None:
    base = _run({"p@5": 0.5, "r@5": 0.5})
    cand = _run({"p@5": 0.7, "r@5": 0.7})
    result = _engine.compare(base, cand)
    assert result.overall_change == pytest.approx(0.2)


def test_compare_run_ids_preserved() -> None:
    base = _run({"p@5": 0.5}, run_id="baseline-run")
    cand = _run({"p@5": 0.7}, run_id="candidate-run")
    result = _engine.compare(base, cand)
    assert result.baseline_run_id == "baseline-run"
    assert result.candidate_run_id == "candidate-run"


def test_compare_metric_in_candidate_only() -> None:
    base = _run({"p@5": 0.5})
    cand = _run({"p@5": 0.7, "r@5": 0.6})
    result = _engine.compare(base, cand)
    names = {mc.metric_name for mc in result.metric_comparisons}
    assert "r@5" in names


def test_compare_empty_both_runs() -> None:
    base = RunResult(run_id="b", metric_results=())
    cand = RunResult(run_id="c", metric_results=())
    result = _engine.compare(base, cand)
    assert result.overall_change == pytest.approx(0.0)
    assert result.metric_comparisons == ()


def test_metric_comparison_fields() -> None:
    mc = MetricComparison(
        metric_name="p@5",
        baseline_mean=0.5,
        candidate_mean=0.8,
        delta=0.3,
    )
    assert mc.metric_name == "p@5"
    assert mc.delta == pytest.approx(0.3)


def test_compare_with_history_uses_average_baseline() -> None:
    h = BenchmarkHistory(
        records=(
            _rec("r1", "2024-01-01", means={"p@5": 0.4}),
            _rec("r2", "2024-01-02", means={"p@5": 0.6}),
        )
    )
    cand = _run({"p@5": 0.7}, run_id="new")
    result = _engine.compare_with_history(cand, h, config_id="cfg")
    comparison = result.metric_comparisons[0]
    assert comparison.baseline_mean == pytest.approx(0.5)
    assert comparison.delta == pytest.approx(0.2)


def test_compare_with_history_empty_raises() -> None:
    h = BenchmarkHistory(records=())
    cand = _run({"p@5": 0.7})
    with pytest.raises(ComparisonError, match="No historical"):
        _engine.compare_with_history(cand, h, config_id="cfg")


def test_compare_with_history_respects_baseline_n() -> None:
    h = BenchmarkHistory(
        records=(
            _rec("r1", "2024-01-01", means={"p@5": 0.1}),
            _rec("r2", "2024-01-02", means={"p@5": 0.5}),
            _rec("r3", "2024-01-03", means={"p@5": 0.9}),
        )
    )
    cand = _run({"p@5": 0.7}, run_id="new")
    result = _engine.compare_with_history(cand, h, config_id="cfg", baseline_n=2)
    comparison = result.metric_comparisons[0]
    assert comparison.baseline_mean == pytest.approx(0.7)
