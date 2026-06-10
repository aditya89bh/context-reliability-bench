from __future__ import annotations

from context_reliability_bench.history import BenchmarkHistory, BenchmarkRunRecord
from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult


def _run(means: dict[str, float], run_id: str = "r") -> RunResult:
    return RunResult(
        run_id=run_id,
        metric_results=tuple(
            MetricResult(
                metric_name=name,
                case_scores=(("c0", m),),
                mean=m,
            )
            for name, m in means.items()
        ),
    )


def _rec(
    run_id: str,
    timestamp: str,
    config_id: str = "cfg",
    tags: frozenset[str] | None = None,
    means: dict[str, float] | None = None,
) -> BenchmarkRunRecord:
    return BenchmarkRunRecord(
        run_result=_run(means or {"p@5": 0.5}, run_id=run_id),
        timestamp=timestamp,
        config_id=config_id,
        tags=tags or frozenset(),
    )


# ─── BenchmarkRunRecord ───────────────────────────────────────────────────────


def test_record_fields() -> None:
    rec = _rec("r", "2024-01-01T00:00:00", config_id="cfg-a")
    assert rec.run_result.run_id == "r"
    assert rec.timestamp == "2024-01-01T00:00:00"
    assert rec.config_id == "cfg-a"


def test_record_default_tags() -> None:
    rec = _rec("r", "2024-01-01T00:00:00")
    assert rec.tags == frozenset()


# ─── BenchmarkHistory ─────────────────────────────────────────────────────────


def test_empty_history() -> None:
    h = BenchmarkHistory(records=())
    assert len(h.records) == 0


def test_add_record() -> None:
    h = BenchmarkHistory(records=())
    h2 = h.add_record(_rec("r1", "2024-01-01T00:00:00"))
    assert len(h2.records) == 1


def test_add_record_does_not_mutate_original() -> None:
    h = BenchmarkHistory(records=())
    h.add_record(_rec("r1", "2024-01-01T00:00:00"))
    assert len(h.records) == 0


def test_filter_by_tag_returns_matching() -> None:
    h = BenchmarkHistory(
        records=(
            _rec("r1", "2024-01-01", tags=frozenset({"ci"})),
            _rec("r2", "2024-01-02", tags=frozenset({"nightly"})),
        )
    )
    filtered = h.filter_by_tag("ci")
    assert len(filtered.records) == 1
    assert filtered.records[0].run_result.run_id == "r1"


def test_filter_by_config_returns_matching() -> None:
    h = BenchmarkHistory(
        records=(
            _rec("r1", "2024-01-01", config_id="A"),
            _rec("r2", "2024-01-02", config_id="B"),
        )
    )
    filtered = h.filter_by_config("A")
    assert len(filtered.records) == 1
    assert filtered.records[0].run_result.run_id == "r1"


def test_filter_by_config_empty_result() -> None:
    h = BenchmarkHistory(records=(_rec("r1", "2024-01-01", config_id="A"),))
    assert len(h.filter_by_config("Z").records) == 0


def test_latest_returns_n_most_recent() -> None:
    h = BenchmarkHistory(
        records=(
            _rec("r1", "2024-01-01T00:00:00"),
            _rec("r2", "2024-01-03T00:00:00"),
            _rec("r3", "2024-01-02T00:00:00"),
        )
    )
    latest = h.latest(2)
    assert len(latest.records) == 2
    timestamps = {r.timestamp for r in latest.records}
    assert "2024-01-03T00:00:00" in timestamps
    assert "2024-01-02T00:00:00" in timestamps


def test_latest_all_when_fewer_than_n() -> None:
    h = BenchmarkHistory(records=(_rec("r1", "2024-01-01"),))
    assert len(h.latest(10).records) == 1


def test_metric_series_returns_ordered() -> None:
    h = BenchmarkHistory(
        records=(
            _rec("r2", "2024-01-02", means={"p@5": 0.7}),
            _rec("r1", "2024-01-01", means={"p@5": 0.5}),
        )
    )
    series = h.metric_series("p@5")
    assert len(series) == 2
    assert series[0] == ("2024-01-01", 0.5)
    assert series[1] == ("2024-01-02", 0.7)


def test_metric_series_missing_metric_skipped() -> None:
    h = BenchmarkHistory(
        records=(
            _rec("r1", "2024-01-01", means={"p@5": 0.5}),
            _rec("r2", "2024-01-02", means={"recall": 0.8}),
        )
    )
    series = h.metric_series("p@5")
    assert len(series) == 1


def test_metric_series_empty_history() -> None:
    h = BenchmarkHistory(records=())
    assert h.metric_series("p@5") == []
