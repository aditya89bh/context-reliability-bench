from __future__ import annotations

from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.quality_gates import (
    GateCheckResult,
    QualityGate,
    QualityGateReport,
    gates_exit_code,
    run_quality_gates,
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


# ─── QualityGate ──────────────────────────────────────────────────────────────


def test_gate_fields() -> None:
    g = QualityGate(metric_name="p@5", min_mean=0.5, description="P@5 ≥ 50%")
    assert g.metric_name == "p@5"
    assert g.min_mean == 0.5
    assert g.description == "P@5 ≥ 50%"


def test_gate_default_description() -> None:
    g = QualityGate(metric_name="p@5", min_mean=0.5)
    assert g.description == ""


# ─── run_quality_gates ────────────────────────────────────────────────────────


def test_gate_passes_when_score_meets_minimum() -> None:
    result = _run({"p@5": 0.7})
    gates = [QualityGate("p@5", min_mean=0.5)]
    report = run_quality_gates(result, gates)
    assert report.all_passed is True


def test_gate_fails_when_score_below_minimum() -> None:
    result = _run({"p@5": 0.3})
    gates = [QualityGate("p@5", min_mean=0.5)]
    report = run_quality_gates(result, gates)
    assert report.all_passed is False


def test_gate_passes_when_score_exactly_minimum() -> None:
    result = _run({"p@5": 0.5})
    gates = [QualityGate("p@5", min_mean=0.5)]
    report = run_quality_gates(result, gates)
    assert report.all_passed is True


def test_all_pass_requires_all_gates() -> None:
    result = _run({"p@5": 0.8, "r@5": 0.3})
    gates = [QualityGate("p@5", min_mean=0.5), QualityGate("r@5", min_mean=0.5)]
    report = run_quality_gates(result, gates)
    assert report.all_passed is False


def test_missing_metric_fails_gate() -> None:
    result = _run({"p@5": 0.8})
    gates = [QualityGate("r@5", min_mean=0.5)]
    report = run_quality_gates(result, gates)
    assert report.all_passed is False
    msg = report.gate_results[0].message
    assert "not found" in msg


def test_report_run_id() -> None:
    result = _run({"p@5": 0.8}, run_id="my-run")
    report = run_quality_gates(result, [QualityGate("p@5", min_mean=0.5)])
    assert report.run_id == "my-run"


def test_failed_gates_list() -> None:
    result = _run({"p@5": 0.3, "r@5": 0.8})
    gates = [QualityGate("p@5", min_mean=0.5), QualityGate("r@5", min_mean=0.5)]
    report = run_quality_gates(result, gates)
    failed = report.failed_gates()
    assert len(failed) == 1
    assert failed[0].gate.metric_name == "p@5"


def test_passed_gates_list() -> None:
    result = _run({"p@5": 0.8, "r@5": 0.3})
    gates = [QualityGate("p@5", min_mean=0.5), QualityGate("r@5", min_mean=0.5)]
    report = run_quality_gates(result, gates)
    passed = report.passed_gates()
    assert len(passed) == 1
    assert passed[0].gate.metric_name == "p@5"


def test_empty_gates_all_pass() -> None:
    result = _run({"p@5": 0.8})
    report = run_quality_gates(result, [])
    assert report.all_passed is True


def test_gate_check_result_message_pass() -> None:
    result = _run({"p@5": 0.8})
    gates = [QualityGate("p@5", min_mean=0.5)]
    report = run_quality_gates(result, gates)
    assert ">=" in report.gate_results[0].message


def test_gate_check_result_message_fail() -> None:
    result = _run({"p@5": 0.3})
    gates = [QualityGate("p@5", min_mean=0.5)]
    report = run_quality_gates(result, gates)
    assert "required" in report.gate_results[0].message


def test_gate_check_actual_score() -> None:
    result = _run({"p@5": 0.75})
    report = run_quality_gates(result, [QualityGate("p@5", min_mean=0.5)])
    assert report.gate_results[0].actual_score == 0.75


# ─── gates_exit_code ──────────────────────────────────────────────────────────


def test_exit_code_zero_when_all_pass() -> None:
    result = _run({"p@5": 0.8})
    report = run_quality_gates(result, [QualityGate("p@5", min_mean=0.5)])
    assert gates_exit_code(report) == 0


def test_exit_code_one_when_any_fails() -> None:
    result = _run({"p@5": 0.3})
    report = run_quality_gates(result, [QualityGate("p@5", min_mean=0.5)])
    assert gates_exit_code(report) == 1


def test_exit_code_zero_for_empty_gates() -> None:
    result = _run({"p@5": 0.8})
    report = run_quality_gates(result, [])
    assert gates_exit_code(report) == 0


def test_quality_gate_report_is_frozen() -> None:
    report = QualityGateReport(run_id="r", gate_results=(), all_passed=True)
    import dataclasses

    try:
        report.run_id = "x"  # type: ignore[misc]
        raise AssertionError("should have raised FrozenInstanceError")
    except dataclasses.FrozenInstanceError:
        pass


def test_gate_check_result_is_frozen() -> None:
    gate = QualityGate("p@5", min_mean=0.5)
    gcr = GateCheckResult(gate=gate, actual_score=0.7, passed=True, message="ok")
    import dataclasses

    try:
        gcr.passed = False  # type: ignore[misc]
        raise AssertionError("should have raised FrozenInstanceError")
    except dataclasses.FrozenInstanceError:
        pass
