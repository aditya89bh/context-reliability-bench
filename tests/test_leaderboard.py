from __future__ import annotations

from context_reliability_bench.models.leaderboard import Leaderboard, LeaderboardEntry


def _entry(
    run_id: str = "run-1",
    system: str = "SystemA",
    scores: tuple[tuple[str, float], ...] = (("p@1", 0.8), ("r@1", 0.6)),
) -> LeaderboardEntry:
    return LeaderboardEntry(
        run_id=run_id, system_name=system, scores=scores
    )


def test_leaderboard_entry_fields() -> None:
    e = _entry()
    assert e.run_id == "run-1"
    assert e.system_name == "SystemA"
    assert len(e.scores) == 2


def test_get_score_hit() -> None:
    e = _entry()
    assert e.get_score("p@1") == 0.8


def test_get_score_miss_returns_none() -> None:
    e = _entry()
    assert e.get_score("ndcg@5") is None


def test_leaderboard_creation() -> None:
    board = Leaderboard(
        benchmark_name="bench",
        entries=(_entry("r1", "Sys1"), _entry("r2", "Sys2")),
    )
    assert board.benchmark_name == "bench"
    assert len(board.entries) == 2


def test_ranked_by_sorts_descending() -> None:
    e1 = _entry("r1", "Sys1", (("p@1", 0.4),))
    e2 = _entry("r2", "Sys2", (("p@1", 0.9),))
    e3 = _entry("r3", "Sys3", (("p@1", 0.6),))
    board = Leaderboard(benchmark_name="b", entries=(e1, e2, e3))
    ranked = board.ranked_by("p@1")
    assert ranked[0].run_id == "r2"
    assert ranked[1].run_id == "r3"
    assert ranked[2].run_id == "r1"


def test_ranked_by_missing_metric_scores_zero() -> None:
    e1 = _entry("r1", "S1", (("p@1", 0.5),))
    e2 = _entry("r2", "S2", (("r@1", 0.9),))
    board = Leaderboard(benchmark_name="b", entries=(e1, e2))
    ranked = board.ranked_by("p@1")
    assert ranked[0].run_id == "r1"
    assert ranked[1].run_id == "r2"


def test_add_entry_returns_new_leaderboard() -> None:
    board = Leaderboard(benchmark_name="b", entries=(_entry("r1", "S1"),))
    new_board = board.add_entry(_entry("r2", "S2"))
    assert len(new_board.entries) == 2
    assert isinstance(new_board, Leaderboard)


def test_add_entry_original_unchanged() -> None:
    e1 = _entry("r1", "S1")
    board = Leaderboard(benchmark_name="b", entries=(e1,))
    board.add_entry(_entry("r2", "S2"))
    assert len(board.entries) == 1


def test_add_entry_preserves_benchmark_name() -> None:
    board = Leaderboard(benchmark_name="my-bench", entries=())
    new_board = board.add_entry(_entry())
    assert new_board.benchmark_name == "my-bench"


def test_empty_leaderboard_ranked_by() -> None:
    board = Leaderboard(benchmark_name="b", entries=())
    assert board.ranked_by("p@1") == []
