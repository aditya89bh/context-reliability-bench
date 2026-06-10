from __future__ import annotations

import pytest

from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.scoring import aggregate_score, category_scores
from context_reliability_bench.suite import SuiteResult


def _run(means: list[float], run_id: str = "r") -> RunResult:
    mrs = tuple(
        MetricResult(
            metric_name=f"m{i}",
            case_scores=(("c0", m),),
            mean=m,
        )
        for i, m in enumerate(means)
    )
    return RunResult(run_id=run_id, metric_results=mrs)


def test_aggregate_score_single_metric() -> None:
    result = _run([0.75])
    assert aggregate_score(result) == pytest.approx(0.75)


def test_aggregate_score_multiple_metrics_mean() -> None:
    result = _run([0.5, 1.0])
    assert aggregate_score(result) == pytest.approx(0.75)


def test_aggregate_score_all_zero() -> None:
    result = _run([0.0, 0.0, 0.0])
    assert aggregate_score(result) == pytest.approx(0.0)


def test_aggregate_score_all_one() -> None:
    result = _run([1.0, 1.0, 1.0])
    assert aggregate_score(result) == pytest.approx(1.0)


def test_aggregate_score_no_metrics_returns_zero() -> None:
    result = RunResult(run_id="r", metric_results=())
    assert aggregate_score(result) == pytest.approx(0.0)


# --- category_scores ---


def _suite() -> SuiteResult:
    r1 = _run([1.0], run_id="cat1")
    r2 = _run([0.5], run_id="cat2")
    return SuiteResult(category_results=(("cat1", r1), ("cat2", r2)))


def test_category_scores_returns_dict() -> None:
    scores = category_scores(_suite())
    assert isinstance(scores, dict)


def test_category_scores_keys() -> None:
    scores = category_scores(_suite())
    assert set(scores.keys()) == {"cat1", "cat2"}


def test_category_scores_values() -> None:
    scores = category_scores(_suite())
    assert scores["cat1"] == pytest.approx(1.0)
    assert scores["cat2"] == pytest.approx(0.5)


def test_category_scores_empty_suite() -> None:
    suite = SuiteResult(category_results=())
    assert category_scores(suite) == {}
