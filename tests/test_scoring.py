from __future__ import annotations

import pytest

from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.scoring import (
    MetricWeight,
    WeightedScoringConfig,
    aggregate_score,
    category_scores,
    weighted_category_scores,
    weighted_score,
)
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


# --- weighted scoring ---


def _config(
    weights: dict[str, float],
    default: float = 1.0,
) -> WeightedScoringConfig:
    return WeightedScoringConfig(
        weights=tuple(
            MetricWeight(metric_name=k, weight=v) for k, v in weights.items()
        ),
        default_weight=default,
    )


def test_metric_weight_fields() -> None:
    mw = MetricWeight(metric_name="p@1", weight=2.0)
    assert mw.metric_name == "p@1"
    assert mw.weight == 2.0


def test_weighted_scoring_config_get_weight_hit() -> None:
    cfg = _config({"p@1": 3.0})
    assert cfg.get_weight("p@1") == pytest.approx(3.0)


def test_weighted_scoring_config_get_weight_default() -> None:
    cfg = _config({"p@1": 3.0}, default=0.5)
    assert cfg.get_weight("r@1") == pytest.approx(0.5)


def test_weighted_score_uniform_equals_aggregate() -> None:
    result = _run([0.4, 0.8])
    cfg = _config({"m0": 1.0, "m1": 1.0})
    assert weighted_score(result, cfg) == pytest.approx(aggregate_score(result))


def test_weighted_score_custom_weights() -> None:
    mr0 = MetricResult(
        metric_name="m0", case_scores=(("c0", 1.0),), mean=1.0
    )
    mr1 = MetricResult(
        metric_name="m1", case_scores=(("c0", 0.0),), mean=0.0
    )
    result = RunResult(run_id="r", metric_results=(mr0, mr1))
    cfg = _config({"m0": 2.0, "m1": 1.0})
    # weighted mean = (1.0*2 + 0.0*1) / 3 = 2/3
    assert weighted_score(result, cfg) == pytest.approx(2.0 / 3.0)


def test_weighted_score_no_metrics() -> None:
    result = RunResult(run_id="r", metric_results=())
    cfg = _config({})
    assert weighted_score(result, cfg) == pytest.approx(0.0)


def test_weighted_category_scores_keys() -> None:
    cfg = _config({})
    scores = weighted_category_scores(_suite(), cfg)
    assert set(scores.keys()) == {"cat1", "cat2"}
