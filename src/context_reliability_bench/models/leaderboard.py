from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeaderboardEntry:
    run_id: str
    system_name: str
    scores: tuple[tuple[str, float], ...]

    def get_score(self, metric_name: str) -> float | None:
        for name, score in self.scores:
            if name == metric_name:
                return score
        return None


@dataclass(frozen=True)
class Leaderboard:
    benchmark_name: str
    entries: tuple[LeaderboardEntry, ...]

    def ranked_by(self, metric_name: str) -> list[LeaderboardEntry]:
        def _key(e: LeaderboardEntry) -> float:
            s = e.get_score(metric_name)
            return s if s is not None else 0.0

        return sorted(self.entries, key=_key, reverse=True)

    def add_entry(self, entry: LeaderboardEntry) -> Leaderboard:
        return Leaderboard(
            benchmark_name=self.benchmark_name,
            entries=(*self.entries, entry),
        )
