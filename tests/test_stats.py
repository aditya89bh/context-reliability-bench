from __future__ import annotations

import math

import pytest

from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.stats import MetricStats, compute_metric_stats, run_stats


def _mr(scores: list[float], name: str = "p@1") -> MetricResult:
    case_scores = tuple((f"c{i}", s) for i, s in enumerate(scores))
    return MetricResult(
        metric_name=name,
        case_scores=case_scores,
        mean=sum(scores) / len(scores),
    )


def test_compute_stats_returns_metric_stats() -> None:
    stats = compute_metric_stats(_mr([0.0, 1.0, 0.5]))
    assert isinstance(stats, MetricStats)


def test_compute_stats_metric_name() -> None:
    stats = compute_metric_stats(_mr([0.5], name="recall@3"))
    assert stats.metric_name == "recall@3"


def test_compute_stats_minimum() -> None:
    stats = compute_metric_stats(_mr([0.2, 0.8, 0.5]))
    assert stats.minimum == pytest.approx(0.2)


def test_compute_stats_maximum() -> None:
    stats = compute_metric_stats(_mr([0.2, 0.8, 0.5]))
    assert stats.maximum == pytest.approx(0.8)


def test_compute_stats_mean() -> None:
    stats = compute_metric_stats(_mr([0.0, 1.0]))
    assert stats.mean == pytest.approx(0.5)


def test_compute_stats_median_odd() -> None:
    stats = compute_metric_stats(_mr([0.1, 0.9, 0.5]))
    assert stats.median == pytest.approx(0.5)


def test_compute_stats_median_even() -> None:
    stats = compute_metric_stats(_mr([0.2, 0.4, 0.6, 0.8]))
    assert stats.median == pytest.approx(0.5)


def test_compute_stats_std_dev_uniform() -> None:
    stats = compute_metric_stats(_mr([0.5, 0.5, 0.5]))
    assert stats.std_dev == pytest.approx(0.0)


def test_compute_stats_std_dev_nonzero() -> None:
    stats = compute_metric_stats(_mr([0.0, 1.0]))
    assert stats.std_dev == pytest.approx(0.5)


def test_compute_stats_single_score_std_dev_zero() -> None:
    stats = compute_metric_stats(_mr([0.7]))
    assert stats.std_dev == pytest.approx(0.0)


def test_compute_stats_std_dev_known_value() -> None:
    scores = [0.0, 0.0, 1.0, 1.0]
    stats = compute_metric_stats(_mr(scores))
    expected_std_dev = math.sqrt(0.25)
    assert stats.std_dev == pytest.approx(expected_std_dev)


def test_run_stats_returns_tuple_per_metric() -> None:
    mr1 = _mr([0.5, 1.0], name="p@1")
    mr2 = _mr([0.3, 0.7], name="r@1")
    result = RunResult(run_id="r", metric_results=(mr1, mr2))
    stats = run_stats(result)
    assert len(stats) == 2


def test_run_stats_metric_names() -> None:
    mr1 = _mr([0.5], name="p@1")
    mr2 = _mr([0.8], name="r@1")
    result = RunResult(run_id="r", metric_results=(mr1, mr2))
    names = {s.metric_name for s in run_stats(result)}
    assert names == {"p@1", "r@1"}
