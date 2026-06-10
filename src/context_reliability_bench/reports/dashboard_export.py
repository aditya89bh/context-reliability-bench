from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from context_reliability_bench.scoring import aggregate_score
from context_reliability_bench.stats import compute_metric_stats
from context_reliability_bench.suite import SuiteResult


def export_dashboard_json(
    suite_result: SuiteResult,
    path: Path,
    run_metadata: dict[str, str] | None = None,
) -> None:
    data = _build_dashboard(suite_result, run_metadata)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _build_dashboard(
    suite_result: SuiteResult,
    run_metadata: dict[str, str] | None,
) -> dict[str, Any]:
    categories: dict[str, Any] = {}
    for name, run in suite_result.category_results:
        metrics: dict[str, Any] = {}
        for mr in run.metric_results:
            st = compute_metric_stats(mr)
            metrics[mr.metric_name] = {
                "mean": mr.mean,
                "minimum": st.minimum,
                "maximum": st.maximum,
                "median": st.median,
                "std_dev": st.std_dev,
                "case_scores": [
                    {"case_id": cid, "score": score}
                    for cid, score in mr.case_scores
                ],
            }
        case_count = (
            len(run.metric_results[0].case_scores)
            if run.metric_results
            else 0
        )
        categories[name] = {
            "run_id": run.run_id,
            "aggregate_score": aggregate_score(run),
            "case_count": case_count,
            "metrics": metrics,
        }

    total_cases = sum(
        v["case_count"] for v in categories.values()
    )
    return {
        "schema_version": "1.0",
        "metadata": run_metadata or {},
        "summary": {
            "total_categories": len(suite_result.category_results),
            "total_cases": total_cases,
        },
        "categories": categories,
    }
