"""Performance tests with generous, stable time budgets.

Each test asserts that the benchmark completes within a wall-clock limit that
is at least 100x the typical measured duration. The goal is to detect runaway
regressions, not to verify speed.
"""

from __future__ import annotations

import pytest

from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext
from context_reliability_bench.runner import run_benchmark
from context_reliability_bench.timing import (
    BenchmarkTiming,
    TimingRecord,
    time_benchmark,
)

# ── corpus generation ────────────────────────────────────────────────────────

_N_SMALL = 50
_N_MEDIUM = 200
_MAX_SECONDS_SMALL = 5.0
_MAX_SECONDS_MEDIUM = 15.0


def _make_rc(doc_id: str, rank: int) -> RetrievedContext:
    return RetrievedContext(
        document=Document(id=doc_id, content=f"Document content for {doc_id}."),
        score=max(0.0, 1.0 - rank * 0.01),
        rank=rank,
    )


def _make_case(case_id: str, n_docs: int = 10) -> BenchmarkCase:
    doc_ids = [f"{case_id}_d{j}" for j in range(n_docs)]
    return BenchmarkCase(
        id=case_id,
        query=Query(id=f"q_{case_id}", text=f"Query for {case_id}"),
        context=tuple(_make_rc(d, i + 1) for i, d in enumerate(doc_ids)),
        relevant_doc_ids=frozenset({doc_ids[0]}),
        expected_answer="N/A",
    )


def _make_cases(n: int, n_docs: int = 10) -> list[BenchmarkCase]:
    return [_make_case(f"c{i:04d}", n_docs=n_docs) for i in range(n)]


# ── TimingRecord / BenchmarkTiming unit tests ────────────────────────────────


def test_timing_record_elapsed_ms() -> None:
    rec = TimingRecord(label="x", elapsed_seconds=1.5)
    assert rec.elapsed_ms == pytest.approx(1500.0)


def test_benchmark_timing_total_seconds() -> None:
    bt = BenchmarkTiming(
        records=(
            TimingRecord(label="a", elapsed_seconds=0.1),
            TimingRecord(label="b", elapsed_seconds=0.2),
        )
    )
    assert bt.total_seconds == pytest.approx(0.3)


def test_benchmark_timing_get_found() -> None:
    rec_in = TimingRecord(label="total", elapsed_seconds=0.5)
    bt = BenchmarkTiming(records=(rec_in,))
    rec = bt.get("total")
    assert rec is not None
    assert rec.elapsed_seconds == pytest.approx(0.5)


def test_benchmark_timing_get_missing() -> None:
    bt = BenchmarkTiming(records=())
    assert bt.get("missing") is None


def test_benchmark_timing_as_dict() -> None:
    bt = BenchmarkTiming(
        records=(
            TimingRecord(label="p@5", elapsed_seconds=0.01),
            TimingRecord(label="total", elapsed_seconds=0.02),
        )
    )
    d = bt.as_dict()
    assert "p@5" in d
    assert "total" in d


def test_time_benchmark_helper() -> None:
    def _add(a: int, b: int) -> int:
        return a + b

    result, rec = time_benchmark(_add, 3, 4, label="add")
    assert result == 7
    assert rec.label == "add"
    assert rec.elapsed_seconds >= 0.0


# ── run_benchmark produces timing ────────────────────────────────────────────


def test_run_benchmark_has_timing() -> None:
    cases = _make_cases(5)
    metrics: list[Metric] = [PrecisionAtK(k=3)]
    result = run_benchmark(cases, metrics)
    assert result.timing is not None


def test_run_benchmark_timing_has_total_record() -> None:
    cases = _make_cases(5)
    metrics: list[Metric] = [PrecisionAtK(k=3)]
    result = run_benchmark(cases, metrics)
    assert result.timing.get("total") is not None


def test_run_benchmark_timing_has_per_metric_record() -> None:
    cases = _make_cases(5)
    metrics: list[Metric] = [PrecisionAtK(k=3), RecallAtK(k=3)]
    result = run_benchmark(cases, metrics)
    assert result.timing.get("precision@3") is not None
    assert result.timing.get("recall@3") is not None


def test_run_benchmark_total_elapsed_positive() -> None:
    cases = _make_cases(10)
    metrics: list[Metric] = [PrecisionAtK(k=5)]
    result = run_benchmark(cases, metrics)
    assert result.timing.total_seconds >= 0.0


# ── wall-clock limits ─────────────────────────────────────────────────────────


def test_small_benchmark_within_time_budget() -> None:
    """50 cases x 3 metrics must complete within 5 seconds."""
    cases = _make_cases(_N_SMALL)
    metrics: list[Metric] = [PrecisionAtK(k=5), RecallAtK(k=5), NdcgAtK(k=5)]
    result = run_benchmark(cases, metrics)
    assert result.timing.total_seconds < _MAX_SECONDS_SMALL, (
        f"Small benchmark took {result.timing.total_seconds:.3f}s "
        f"(limit {_MAX_SECONDS_SMALL}s)"
    )


def test_medium_benchmark_within_time_budget() -> None:
    """200 cases x 3 metrics must complete within 15 seconds."""
    cases = _make_cases(_N_MEDIUM)
    metrics: list[Metric] = [PrecisionAtK(k=5), RecallAtK(k=5), NdcgAtK(k=5)]
    result = run_benchmark(cases, metrics)
    assert result.timing.total_seconds < _MAX_SECONDS_MEDIUM, (
        f"Medium benchmark took {result.timing.total_seconds:.3f}s "
        f"(limit {_MAX_SECONDS_MEDIUM}s)"
    )


def test_timing_record_count_equals_metrics_plus_total() -> None:
    cases = _make_cases(5)
    metrics: list[Metric] = [PrecisionAtK(k=3), RecallAtK(k=3), NdcgAtK(k=3)]
    result = run_benchmark(cases, metrics)
    assert len(result.timing.records) == len(metrics) + 1
