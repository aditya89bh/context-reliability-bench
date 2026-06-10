from __future__ import annotations

import csv
import json
from pathlib import Path

from context_reliability_bench.models.leaderboard import Leaderboard, LeaderboardEntry
from context_reliability_bench.models.run_result import RunResult


def build_leaderboard_entry(
    result: RunResult,
    system_name: str,
) -> LeaderboardEntry:
    scores = tuple((mr.metric_name, mr.mean) for mr in result.metric_results)
    return LeaderboardEntry(
        run_id=result.run_id,
        system_name=system_name,
        scores=scores,
    )


def export_leaderboard_json(board: Leaderboard, path: Path) -> None:
    data = {
        "benchmark_name": board.benchmark_name,
        "entries": [
            {
                "run_id": entry.run_id,
                "system_name": entry.system_name,
                "scores": {name: score for name, score in entry.scores},
            }
            for entry in board.entries
        ],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def export_leaderboard_csv(board: Leaderboard, path: Path) -> None:
    metric_names = sorted(
        {name for entry in board.entries for name, _ in entry.scores}
    )
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", "system_name"] + metric_names)
        for entry in board.entries:
            score_map = dict(entry.scores)
            row: list[str | float] = [entry.run_id, entry.system_name]
            for m in metric_names:
                row.append(score_map.get(m, 0.0))
            writer.writerow(row)
