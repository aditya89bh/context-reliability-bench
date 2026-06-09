from __future__ import annotations

import csv
from pathlib import Path

from context_reliability_bench.models.run_result import RunResult


def export_csv(result: RunResult, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", "metric", "case_id", "score"])
        for mr in result.metric_results:
            for case_id, score in mr.case_scores:
                writer.writerow([result.run_id, mr.metric_name, case_id, score])
