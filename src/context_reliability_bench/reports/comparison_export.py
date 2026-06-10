from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from context_reliability_bench.models.run_result import RunResult


@dataclass(frozen=True)
class MetricDelta:
    metric_name: str
    baseline_mean: float
    candidate_mean: float
    delta: float
    improved: bool


def compare_runs(
    baseline: RunResult,
    candidate: RunResult,
) -> tuple[MetricDelta, ...]:
    baseline_map = {mr.metric_name: mr.mean for mr in baseline.metric_results}
    candidate_map = {mr.metric_name: mr.mean for mr in candidate.metric_results}
    all_metrics = sorted(baseline_map.keys() | candidate_map.keys())
    deltas: list[MetricDelta] = []
    for name in all_metrics:
        b = baseline_map.get(name, 0.0)
        c = candidate_map.get(name, 0.0)
        d = c - b
        deltas.append(
            MetricDelta(
                metric_name=name,
                baseline_mean=b,
                candidate_mean=c,
                delta=d,
                improved=d > 0,
            )
        )
    return tuple(deltas)


def export_comparison_json(
    baseline: RunResult,
    candidate: RunResult,
    path: Path,
) -> None:
    deltas = compare_runs(baseline, candidate)
    data = {
        "baseline_run_id": baseline.run_id,
        "candidate_run_id": candidate.run_id,
        "metrics": [
            {
                "metric_name": d.metric_name,
                "baseline_mean": d.baseline_mean,
                "candidate_mean": d.candidate_mean,
                "delta": d.delta,
                "improved": d.improved,
            }
            for d in deltas
        ],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def export_comparison_markdown(
    baseline: RunResult,
    candidate: RunResult,
    path: Path,
) -> None:
    deltas = compare_runs(baseline, candidate)
    lines: list[str] = [
        "# Benchmark Comparison",
        "",
        f"- **Baseline:** {baseline.run_id}",
        f"- **Candidate:** {candidate.run_id}",
        "",
        "## Metric Comparison",
        "",
        "| Metric | Baseline | Candidate | Delta | Change |",
        "| --- | --- | --- | --- | --- |",
    ]
    for d in deltas:
        if d.improved:
            change = "improved"
        elif d.delta < 0:
            change = "regressed"
        else:
            change = "unchanged"
        lines.append(
            f"| {d.metric_name} "
            f"| {d.baseline_mean:.4f} "
            f"| {d.candidate_mean:.4f} "
            f"| {d.delta:+.4f} "
            f"| {change} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
