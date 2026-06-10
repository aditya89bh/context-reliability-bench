from __future__ import annotations

from dataclasses import dataclass

from context_reliability_bench.models.run_result import RunResult


@dataclass(frozen=True)
class RegressionThreshold:
    metric_name: str
    max_absolute_drop: float = 0.05
    max_relative_drop: float = 0.10


@dataclass(frozen=True)
class RegressionResult:
    metric_name: str
    baseline_score: float
    current_score: float
    regression_detected: bool
    reason: str


@dataclass(frozen=True)
class RegressionReport:
    run_id: str
    regressions: tuple[RegressionResult, ...]
    has_regressions: bool

    def detected(self) -> list[RegressionResult]:
        return [r for r in self.regressions if r.regression_detected]


class RegressionDetector:
    def __init__(
        self,
        thresholds: list[RegressionThreshold] | None = None,
        default_max_absolute_drop: float = 0.05,
        default_max_relative_drop: float = 0.10,
    ) -> None:
        self._thresholds = {t.metric_name: t for t in (thresholds or [])}
        self._default_abs = default_max_absolute_drop
        self._default_rel = default_max_relative_drop

    def detect(
        self,
        current: RunResult,
        baseline: RunResult,
    ) -> RegressionReport:
        baseline_map = {mr.metric_name: mr.mean for mr in baseline.metric_results}
        results: list[RegressionResult] = []

        for mr in current.metric_results:
            t = self._thresholds.get(mr.metric_name)
            abs_threshold = t.max_absolute_drop if t else self._default_abs
            rel_threshold = t.max_relative_drop if t else self._default_rel

            baseline_score = baseline_map.get(mr.metric_name, mr.mean)
            drop = baseline_score - mr.mean
            regression = False
            reason = ""

            if drop > abs_threshold:
                regression = True
                reason = (
                    f"absolute drop {drop:.4f} exceeds threshold {abs_threshold:.4f}"
                )
            elif baseline_score > 0 and (drop / baseline_score) > rel_threshold:
                regression = True
                rel = drop / baseline_score
                reason = (
                    f"relative drop {rel:.1%} exceeds threshold {rel_threshold:.1%}"
                )

            results.append(
                RegressionResult(
                    metric_name=mr.metric_name,
                    baseline_score=baseline_score,
                    current_score=mr.mean,
                    regression_detected=regression,
                    reason=reason,
                )
            )

        return RegressionReport(
            run_id=current.run_id,
            regressions=tuple(results),
            has_regressions=any(r.regression_detected for r in results),
        )
