from __future__ import annotations

import json
from pathlib import Path

from context_reliability_bench.models.run_result import RunResult


def export_json(result: RunResult, path: Path) -> None:
    data = {
        "run_id": result.run_id,
        "metrics": {
            mr.metric_name: {
                "mean": mr.mean,
                "case_scores": [
                    {"case_id": cid, "score": score}
                    for cid, score in mr.case_scores
                ],
            }
            for mr in result.metric_results
        },
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
