"""
Report generation example.

Run with:
    python examples/generate_reports.py

Demonstrates: exporting HTML, Markdown, JSON, CSV reports and a dashboard
JSON from a multi-category suite result.
"""

from __future__ import annotations

import sys
from pathlib import Path

from context_reliability_bench.metrics.mrr import ReciprocalRank
from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.metrics.top_k_accuracy import TopKAccuracy
from context_reliability_bench.reports import (
    export_comparison_json,
    export_comparison_markdown,
    export_csv,
    export_dashboard_json,
    export_html,
    export_json,
    export_markdown,
)
from context_reliability_bench.suite import build_default_registry, run_suite

_ROOT = Path(__file__).parent.parent
_OUT = _ROOT / "examples" / "output" / "reports"


def main() -> int:
    print("=== Report Generation Example ===\n")

    # ── 1. Run multi-category suite ────────────────────────────────────────────
    registry = build_default_registry()
    k = 5
    metrics: list[Metric] = [
        PrecisionAtK(k=k),
        RecallAtK(k=k),
        NdcgAtK(k=k),
        ReciprocalRank(),
        TopKAccuracy(k=k),
    ]

    print(f"Running suite across {len(registry)} categories …")
    suite_result = run_suite(registry, metrics)
    print(f"Done.  Categories evaluated: {suite_result.names()}\n")

    _OUT.mkdir(parents=True, exist_ok=True)

    # ── 2. Per-category reports ────────────────────────────────────────────────
    for cat_name, run_result in suite_result.category_results:
        cat_dir = _OUT / cat_name
        cat_dir.mkdir(parents=True, exist_ok=True)

        export_html(run_result, cat_dir / "report.html")
        export_markdown(run_result, cat_dir / "report.md")
        export_json(run_result, cat_dir / "report.json")
        export_csv(run_result, cat_dir / "report.csv")
        print(f"  {cat_name}: HTML, Markdown, JSON, CSV")

    # ── 3. Dashboard export ────────────────────────────────────────────────────
    dashboard_path = _OUT / "dashboard.json"
    export_dashboard_json(
        suite_result,
        dashboard_path,
        run_metadata={"run_id": "example-suite", "k": str(k)},
    )
    print(f"\nDashboard  → {dashboard_path.relative_to(_ROOT)}")

    # ── 4. Comparison report (first two categories) ────────────────────────────
    names = suite_result.names()
    if len(names) >= 2:
        cat_a = suite_result.get(names[0])
        cat_b = suite_result.get(names[1])
        if cat_a is not None and cat_b is not None:
            comp_json = _OUT / "comparison.json"
            comp_md = _OUT / "comparison.md"
            export_comparison_json(cat_a, cat_b, comp_json)
            export_comparison_markdown(cat_a, cat_b, comp_md)
            print(
                f"Comparison ({names[0]} vs {names[1]}) → "
                f"{comp_json.relative_to(_ROOT)}"
            )

    print(f"\nAll reports written to {_OUT.relative_to(_ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
