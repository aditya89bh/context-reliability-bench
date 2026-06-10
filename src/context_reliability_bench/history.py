from __future__ import annotations

from dataclasses import dataclass, field

from context_reliability_bench.models.run_result import RunResult


def _empty_frozenset() -> frozenset[str]:
    return frozenset()


@dataclass(frozen=True)
class BenchmarkRunRecord:
    run_result: RunResult
    timestamp: str
    config_id: str
    tags: frozenset[str] = field(default_factory=_empty_frozenset)


@dataclass(frozen=True)
class BenchmarkHistory:
    records: tuple[BenchmarkRunRecord, ...]

    def add_record(self, record: BenchmarkRunRecord) -> BenchmarkHistory:
        return BenchmarkHistory(records=self.records + (record,))

    def filter_by_tag(self, tag: str) -> BenchmarkHistory:
        return BenchmarkHistory(
            records=tuple(r for r in self.records if tag in r.tags)
        )

    def filter_by_config(self, config_id: str) -> BenchmarkHistory:
        return BenchmarkHistory(
            records=tuple(r for r in self.records if r.config_id == config_id)
        )

    def latest(self, n: int = 10) -> BenchmarkHistory:
        sorted_recs = sorted(
            self.records, key=lambda r: r.timestamp, reverse=True
        )
        return BenchmarkHistory(records=tuple(sorted_recs[:n]))

    def metric_series(
        self, metric_name: str
    ) -> list[tuple[str, float]]:
        """Return (timestamp, mean) pairs for the given metric, oldest first."""
        sorted_recs = sorted(self.records, key=lambda r: r.timestamp)
        series: list[tuple[str, float]] = []
        for record in sorted_recs:
            for mr in record.run_result.metric_results:
                if mr.metric_name == metric_name:
                    series.append((record.timestamp, mr.mean))
                    break
        return series
