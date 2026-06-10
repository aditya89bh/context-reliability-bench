from __future__ import annotations

from dataclasses import dataclass

from context_reliability_bench.history import BenchmarkHistory
from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult


class ComparisonError(Exception):
    pass


@dataclass(frozen=True)
class MetricComparison:
    metric_name: str
    baseline_mean: float
    candidate_mean: float
    delta: float


@dataclass(frozen=True)
class ComparisonResult:
    baseline_run_id: str
    candidate_run_id: str
    metric_comparisons: tuple[MetricComparison, ...]
    improved_metrics: tuple[str, ...]
    regressed_metrics: tuple[str, ...]
    overall_change: float


class BenchmarkComparisonEngine:
    def compare(
        self,
        baseline: RunResult,
        candidate: RunResult,
    ) -> ComparisonResult:
        baseline_map = {mr.metric_name: mr.mean for mr in baseline.metric_results}
        candidate_map = {mr.metric_name: mr.mean for mr in candidate.metric_results}
        all_names = sorted(baseline_map.keys() | candidate_map.keys())

        comparisons: list[MetricComparison] = []
        for name in all_names:
            b = baseline_map.get(name, 0.0)
            c = candidate_map.get(name, 0.0)
            comparisons.append(
                MetricComparison(
                    metric_name=name,
                    baseline_mean=b,
                    candidate_mean=c,
                    delta=c - b,
                )
            )

        improved = tuple(mc.metric_name for mc in comparisons if mc.delta > 0)
        regressed = tuple(mc.metric_name for mc in comparisons if mc.delta < 0)
        overall = (
            sum(mc.delta for mc in comparisons) / len(comparisons)
            if comparisons
            else 0.0
        )

        return ComparisonResult(
            baseline_run_id=baseline.run_id,
            candidate_run_id=candidate.run_id,
            metric_comparisons=tuple(comparisons),
            improved_metrics=improved,
            regressed_metrics=regressed,
            overall_change=overall,
        )

    def compare_with_history(
        self,
        candidate: RunResult,
        history: BenchmarkHistory,
        config_id: str,
        baseline_n: int = 3,
    ) -> ComparisonResult:
        filtered = history.filter_by_config(config_id)
        recent = filtered.latest(baseline_n)
        if not recent.records:
            raise ComparisonError(
                f"No historical records found for config_id='{config_id}'"
            )

        metric_sums: dict[str, list[float]] = {}
        for record in recent.records:
            for mr in record.run_result.metric_results:
                metric_sums.setdefault(mr.metric_name, []).append(mr.mean)

        baseline_mrs: tuple[MetricResult, ...] = tuple(
            MetricResult(
                metric_name=name,
                case_scores=(),
                mean=sum(vals) / len(vals),
            )
            for name, vals in metric_sums.items()
        )
        baseline = RunResult(
            run_id=f"history_avg({config_id},n={len(recent.records)})",
            metric_results=baseline_mrs,
        )
        return self.compare(baseline, candidate)
