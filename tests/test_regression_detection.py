from __future__ import annotations

from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.regression import (
    RegressionDetector,
    RegressionReport,
    RegressionResult,
    RegressionThreshold,
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


# ─── RegressionThreshold ─────────────────────────────────────────────────────


def test_threshold_defaults() -> None:
    t = RegressionThreshold(metric_name="p@5")
    assert t.max_absolute_drop == 0.05
    assert t.max_relative_drop == 0.10


def test_threshold_custom() -> None:
    t = RegressionThreshold("p@5", max_absolute_drop=0.02, max_relative_drop=0.05)
    assert t.max_absolute_drop == 0.02
    assert t.max_relative_drop == 0.05


# ─── RegressionDetector ──────────────────────────────────────────────────────


def test_no_regression_when_score_unchanged() -> None:
    detector = RegressionDetector()
    baseline = _run({"p@5": 0.8})
    current = _run({"p@5": 0.8})
    report = detector.detect(current, baseline)
    assert not report.has_regressions


def test_no_regression_when_score_improved() -> None:
    detector = RegressionDetector()
    baseline = _run({"p@5": 0.5})
    current = _run({"p@5": 0.8})
    report = detector.detect(current, baseline)
    assert not report.has_regressions


def test_regression_detected_for_large_absolute_drop() -> None:
    detector = RegressionDetector(default_max_absolute_drop=0.05)
    baseline = _run({"p@5": 0.8})
    current = _run({"p@5": 0.6})
    report = detector.detect(current, baseline)
    assert report.has_regressions
    assert report.detected()[0].metric_name == "p@5"


def test_no_regression_for_small_absolute_drop() -> None:
    detector = RegressionDetector(default_max_absolute_drop=0.05)
    baseline = _run({"p@5": 0.8})
    current = _run({"p@5": 0.78})
    report = detector.detect(current, baseline)
    assert not report.has_regressions


def test_regression_detected_for_relative_drop() -> None:
    detector = RegressionDetector(
        default_max_absolute_drop=0.5,
        default_max_relative_drop=0.10,
    )
    baseline = _run({"p@5": 0.8})
    current = _run({"p@5": 0.6})
    report = detector.detect(current, baseline)
    assert report.has_regressions


def test_per_metric_threshold_overrides_default() -> None:
    custom = RegressionThreshold("p@5", max_absolute_drop=0.001)
    detector = RegressionDetector(thresholds=[custom])
    baseline = _run({"p@5": 0.8})
    current = _run({"p@5": 0.799})
    report = detector.detect(current, baseline)
    assert report.has_regressions


def test_report_run_id_from_current() -> None:
    detector = RegressionDetector()
    baseline = _run({"p@5": 0.8})
    current = _run({"p@5": 0.7}, run_id="my-run")
    report = detector.detect(current, baseline)
    assert report.run_id == "my-run"


def test_report_detected_list() -> None:
    detector = RegressionDetector(default_max_absolute_drop=0.05)
    baseline = _run({"p@5": 0.8, "r@5": 0.7})
    current = _run({"p@5": 0.6, "r@5": 0.69})
    report = detector.detect(current, baseline)
    detected = report.detected()
    assert len(detected) == 1
    assert detected[0].metric_name == "p@5"


def test_regression_result_fields() -> None:
    rr = RegressionResult(
        metric_name="p@5",
        baseline_score=0.8,
        current_score=0.6,
        regression_detected=True,
        reason="dropped",
    )
    assert rr.baseline_score == 0.8
    assert rr.current_score == 0.6
    assert rr.regression_detected is True


def test_report_is_frozen() -> None:
    report = RegressionReport(run_id="r", regressions=(), has_regressions=False)
    import dataclasses

    try:
        report.run_id = "other"  # type: ignore[misc]
        raise AssertionError("should have raised FrozenInstanceError")
    except dataclasses.FrozenInstanceError:
        pass


def test_metric_not_in_baseline_uses_current_as_baseline() -> None:
    detector = RegressionDetector()
    baseline = _run({"r@5": 0.5})
    current = _run({"p@5": 0.7, "r@5": 0.5})
    report = detector.detect(current, baseline)
    p_result = next(r for r in report.regressions if r.metric_name == "p@5")
    assert not p_result.regression_detected
