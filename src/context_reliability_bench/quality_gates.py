from __future__ import annotations

from dataclasses import dataclass

from context_reliability_bench.models.run_result import RunResult


@dataclass(frozen=True)
class QualityGate:
    metric_name: str
    min_mean: float
    description: str = ""


@dataclass(frozen=True)
class GateCheckResult:
    gate: QualityGate
    actual_score: float
    passed: bool
    message: str


@dataclass(frozen=True)
class QualityGateReport:
    run_id: str
    gate_results: tuple[GateCheckResult, ...]
    all_passed: bool

    def failed_gates(self) -> list[GateCheckResult]:
        return [r for r in self.gate_results if not r.passed]

    def passed_gates(self) -> list[GateCheckResult]:
        return [r for r in self.gate_results if r.passed]


def run_quality_gates(
    result: RunResult,
    gates: list[QualityGate],
) -> QualityGateReport:
    metric_map = {mr.metric_name: mr.mean for mr in result.metric_results}
    check_results: list[GateCheckResult] = []

    for gate in gates:
        actual = metric_map.get(gate.metric_name)
        if actual is None:
            check_results.append(
                GateCheckResult(
                    gate=gate,
                    actual_score=0.0,
                    passed=False,
                    message=(
                        f"Metric '{gate.metric_name}' not found in run results"
                    ),
                )
            )
            continue

        passed = actual >= gate.min_mean
        if passed:
            msg = (
                f"{gate.metric_name}: {actual:.4f} >= {gate.min_mean:.4f}"
            )
        else:
            msg = (
                f"{gate.metric_name}: {actual:.4f} < {gate.min_mean:.4f}"
                " (required)"
            )
        check_results.append(
            GateCheckResult(gate=gate, actual_score=actual, passed=passed, message=msg)
        )

    return QualityGateReport(
        run_id=result.run_id,
        gate_results=tuple(check_results),
        all_passed=all(r.passed for r in check_results),
    )


def gates_exit_code(report: QualityGateReport) -> int:
    """Return 0 if all gates pass, 1 if any fail. Suitable for CI exit codes."""
    return 0 if report.all_passed else 1
