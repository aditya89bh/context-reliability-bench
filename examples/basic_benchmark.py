"""
Basic benchmark example.

Run with:
    python examples/basic_benchmark.py

Demonstrates: loading a fixture, running multiple metrics, exporting a JSON report,
and checking quality gates.
"""

from __future__ import annotations

import sys
from pathlib import Path

from context_reliability_bench.loader import load_fixture
from context_reliability_bench.metrics.mrr import ReciprocalRank
from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.metrics.top_k_accuracy import TopKAccuracy
from context_reliability_bench.quality_gates import (
    QualityGate,
    gates_exit_code,
    run_quality_gates,
)
from context_reliability_bench.reports import export_json, export_markdown
from context_reliability_bench.runner import run_benchmark
from context_reliability_bench.scoring import aggregate_score
from context_reliability_bench.stats import run_stats

_ROOT = Path(__file__).parent.parent
_FIXTURE = _ROOT / "fixtures" / "sample.json"


def main() -> int:
    print("=== Basic Benchmark Example ===\n")

    # ── 1. Load fixture ────────────────────────────────────────────────────────
    cases = load_fixture(_FIXTURE)
    print(f"Loaded {len(cases)} benchmark cases from {_FIXTURE.name}\n")

    # ── 2. Define metrics ──────────────────────────────────────────────────────
    k = 5
    metrics: list[Metric] = [
        PrecisionAtK(k=k),
        RecallAtK(k=k),
        NdcgAtK(k=k),
        ReciprocalRank(),
        TopKAccuracy(k=k),
    ]

    # ── 3. Run benchmark ───────────────────────────────────────────────────────
    result = run_benchmark(cases, metrics, run_id="basic-example")

    # ── 4. Print per-metric summary ────────────────────────────────────────────
    print("── Metric Results ──────────────────────────────")
    for mr in result.metric_results:
        print(f"  {mr.metric_name:<20} mean={mr.mean:.4f}")

    print(f"\n  Aggregate score: {aggregate_score(result):.4f}\n")

    # ── 5. Print statistics ────────────────────────────────────────────────────
    print("── Statistics ──────────────────────────────────")
    for stat in run_stats(result):
        print(
            f"  {stat.metric_name:<20} "
            f"min={stat.minimum:.4f}  max={stat.maximum:.4f}  "
            f"std={stat.std_dev:.4f}"
        )

    # ── 6. Export reports ──────────────────────────────────────────────────────
    out_dir = _ROOT / "examples" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "basic_result.json"
    md_path = out_dir / "basic_result.md"
    export_json(result, json_path)
    export_markdown(result, md_path)
    print(f"\nReports written to {out_dir}/")

    # ── 7. Quality gates ───────────────────────────────────────────────────────
    print("\n── Quality Gates ───────────────────────────────")
    gates = [
        QualityGate(f"precision@{k}", min_mean=0.10, description="P@K baseline"),
        QualityGate(f"recall@{k}", min_mean=0.10, description="R@K baseline"),
    ]
    gate_report = run_quality_gates(result, gates)
    for gr in gate_report.gate_results:
        icon = "PASS" if gr.passed else "FAIL"
        print(f"  [{icon}] {gr.message}")

    print(f"\nAll gates passed: {gate_report.all_passed}")
    return gates_exit_code(gate_report)


if __name__ == "__main__":
    sys.exit(main())
