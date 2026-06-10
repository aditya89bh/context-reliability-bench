from __future__ import annotations

import pytest

from context_reliability_bench.history import BenchmarkHistory, BenchmarkRunRecord
from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.trend import (
    TrendAnalysis,
    _linear_slope,
    analyze_trends,
)


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


def _history(*entries: tuple[str, dict[str, float]]) -> BenchmarkHistory:
    records = tuple(
        BenchmarkRunRecord(
            run_result=_run(means),
            timestamp=ts,
            config_id="cfg",
        )
        for ts, means in entries
    )
    return BenchmarkHistory(records=records)


# ─── _linear_slope ────────────────────────────────────────────────────────────


def test_slope_increasing() -> None:
    slope = _linear_slope([0.1, 0.2, 0.3])
    assert slope == pytest.approx(0.1)


def test_slope_decreasing() -> None:
    slope = _linear_slope([0.3, 0.2, 0.1])
    assert slope == pytest.approx(-0.1)


def test_slope_flat() -> None:
    slope = _linear_slope([0.5, 0.5, 0.5])
    assert slope == pytest.approx(0.0)


def test_slope_single_value_is_zero() -> None:
    assert _linear_slope([0.9]) == pytest.approx(0.0)


# ─── analyze_trends ───────────────────────────────────────────────────────────


def test_single_record_returns_empty_analysis() -> None:
    h = _history(("2024-01-01", {"p@5": 0.5}))
    result = analyze_trends(h)
    assert result.metric_trends == ()


def test_two_records_produces_trend() -> None:
    h = _history(
        ("2024-01-01", {"p@5": 0.5}),
        ("2024-01-02", {"p@5": 0.7}),
    )
    result = analyze_trends(h)
    assert len(result.metric_trends) == 1


def test_improving_direction() -> None:
    h = _history(
        ("2024-01-01", {"p@5": 0.1}),
        ("2024-01-02", {"p@5": 0.5}),
        ("2024-01-03", {"p@5": 0.9}),
    )
    result = analyze_trends(h)
    trend = result.get_trend("p@5")
    assert trend is not None
    assert trend.direction == "improving"


def test_degrading_direction() -> None:
    h = _history(
        ("2024-01-01", {"p@5": 0.9}),
        ("2024-01-02", {"p@5": 0.5}),
        ("2024-01-03", {"p@5": 0.1}),
    )
    result = analyze_trends(h)
    trend = result.get_trend("p@5")
    assert trend is not None
    assert trend.direction == "degrading"


def test_stable_direction() -> None:
    h = _history(
        ("2024-01-01", {"p@5": 0.5}),
        ("2024-01-02", {"p@5": 0.5}),
        ("2024-01-03", {"p@5": 0.5}),
    )
    result = analyze_trends(h)
    trend = result.get_trend("p@5")
    assert trend is not None
    assert trend.direction == "stable"


def test_values_ordered_oldest_first() -> None:
    h = _history(
        ("2024-01-03", {"p@5": 0.9}),
        ("2024-01-01", {"p@5": 0.5}),
        ("2024-01-02", {"p@5": 0.7}),
    )
    result = analyze_trends(h)
    trend = result.get_trend("p@5")
    assert trend is not None
    assert trend.values == (0.5, 0.7, 0.9)


def test_explicit_metric_names() -> None:
    h = _history(
        ("2024-01-01", {"p@5": 0.5, "r@5": 0.4}),
        ("2024-01-02", {"p@5": 0.7, "r@5": 0.5}),
    )
    result = analyze_trends(h, metric_names=["p@5"])
    names = {t.metric_name for t in result.metric_trends}
    assert names == {"p@5"}


def test_get_trend_found() -> None:
    h = _history(
        ("2024-01-01", {"p@5": 0.5}),
        ("2024-01-02", {"p@5": 0.7}),
    )
    result = analyze_trends(h)
    assert result.get_trend("p@5") is not None


def test_get_trend_not_found() -> None:
    result = TrendAnalysis(metric_trends=())
    assert result.get_trend("nonexistent") is None


def test_metric_not_present_in_all_runs_skipped() -> None:
    h = _history(
        ("2024-01-01", {"p@5": 0.5}),
        ("2024-01-02", {"r@5": 0.7}),
    )
    result = analyze_trends(h)
    p_trend = result.get_trend("p@5")
    assert p_trend is None
