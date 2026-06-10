from __future__ import annotations

import json
from pathlib import Path

from context_reliability_bench.leaderboard_export import (
    build_leaderboard_entry,
    export_leaderboard_csv,
    export_leaderboard_json,
)
from context_reliability_bench.models.leaderboard import Leaderboard, LeaderboardEntry
from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult


def _run_result(run_id: str = "run-1") -> RunResult:
    mr = MetricResult(
        metric_name="precision@1",
        case_scores=(("c1", 1.0), ("c2", 0.0)),
        mean=0.5,
    )
    return RunResult(run_id=run_id, metric_results=(mr,))


def _board() -> Leaderboard:
    e1 = LeaderboardEntry(
        run_id="r1",
        system_name="SysA",
        scores=(("precision@1", 0.8),),
    )
    e2 = LeaderboardEntry(
        run_id="r2",
        system_name="SysB",
        scores=(("precision@1", 0.6),),
    )
    return Leaderboard(benchmark_name="noise_bench", entries=(e1, e2))


def test_build_entry_returns_leaderboard_entry() -> None:
    entry = build_leaderboard_entry(_run_result(), "MySystem")
    assert isinstance(entry, LeaderboardEntry)


def test_build_entry_run_id() -> None:
    entry = build_leaderboard_entry(_run_result("run-42"), "S")
    assert entry.run_id == "run-42"


def test_build_entry_system_name() -> None:
    entry = build_leaderboard_entry(_run_result(), "GPT-RAG")
    assert entry.system_name == "GPT-RAG"


def test_build_entry_scores_match_run_result() -> None:
    result = _run_result()
    entry = build_leaderboard_entry(result, "S")
    score_map = dict(entry.scores)
    assert score_map["precision@1"] == 0.5


def test_json_export_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "leaderboard.json"
    export_leaderboard_json(_board(), out)
    assert out.exists()


def test_json_export_structure(tmp_path: Path) -> None:
    out = tmp_path / "leaderboard.json"
    export_leaderboard_json(_board(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["benchmark_name"] == "noise_bench"
    assert len(data["entries"]) == 2


def test_json_export_entry_fields(tmp_path: Path) -> None:
    out = tmp_path / "leaderboard.json"
    export_leaderboard_json(_board(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    entry = data["entries"][0]
    assert "run_id" in entry
    assert "system_name" in entry
    assert "scores" in entry


def test_csv_export_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "leaderboard.csv"
    export_leaderboard_csv(_board(), out)
    assert out.exists()


def test_csv_export_header(tmp_path: Path) -> None:
    out = tmp_path / "leaderboard.csv"
    export_leaderboard_csv(_board(), out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "run_id,system_name,precision@1"


def test_csv_export_row_count(tmp_path: Path) -> None:
    out = tmp_path / "leaderboard.csv"
    export_leaderboard_csv(_board(), out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3  # header + 2 entries
