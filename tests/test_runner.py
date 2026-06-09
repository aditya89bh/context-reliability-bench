from __future__ import annotations

import pytest

from context_reliability_bench.loader import load_fixture
from context_reliability_bench.metrics.mrr import ReciprocalRank
from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.metrics.top_k_accuracy import TopKAccuracy
from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext
from context_reliability_bench.runner import run_benchmark

FIXTURES_DIR = (
    __import__("pathlib").Path(__file__).parent.parent / "fixtures"
)


def _rc(doc_id: str, rank: int) -> RetrievedContext:
    return RetrievedContext(
        document=Document(id=doc_id, content=f"Content of {doc_id}."),
        score=1.0 - rank * 0.1,
        rank=rank,
    )


def _case(
    case_id: str,
    doc_ids: list[str],
    relevant_ids: frozenset[str],
) -> BenchmarkCase:
    return BenchmarkCase(
        id=case_id,
        query=Query(id=f"q-{case_id}", text="A question?"),
        context=tuple(_rc(d, i + 1) for i, d in enumerate(doc_ids)),
        relevant_doc_ids=relevant_ids,
        expected_answer="answer",
    )


CASE_HIT = _case("c1", ["d1", "d2", "d3"], frozenset({"d1"}))
CASE_MISS = _case("c2", ["d1", "d2", "d3"], frozenset({"d99"}))


def test_run_single_metric_name() -> None:
    result = run_benchmark([CASE_HIT], [PrecisionAtK(k=1)])
    assert result.metric_results[0].metric_name == "precision@1"


def test_run_single_metric_count() -> None:
    result = run_benchmark([CASE_HIT], [PrecisionAtK(k=1)])
    assert len(result.metric_results) == 1


def test_run_multiple_metrics_count() -> None:
    metrics: list[Metric] = [PrecisionAtK(k=3), RecallAtK(k=3), ReciprocalRank()]
    result = run_benchmark([CASE_HIT], metrics)
    assert len(result.metric_results) == 3


def test_run_case_scores_length() -> None:
    cases = [CASE_HIT, CASE_MISS]
    result = run_benchmark(cases, [PrecisionAtK(k=1)])
    assert len(result.metric_results[0].case_scores) == 2


def test_run_case_score_ids_match() -> None:
    cases = [CASE_HIT, CASE_MISS]
    result = run_benchmark(cases, [PrecisionAtK(k=1)])
    ids = [cid for cid, _ in result.metric_results[0].case_scores]
    assert ids == ["c1", "c2"]


def test_run_precision_hit_score() -> None:
    result = run_benchmark([CASE_HIT], [PrecisionAtK(k=1)])
    _, score = result.metric_results[0].case_scores[0]
    assert score == pytest.approx(1.0)


def test_run_precision_miss_score() -> None:
    result = run_benchmark([CASE_MISS], [PrecisionAtK(k=1)])
    _, score = result.metric_results[0].case_scores[0]
    assert score == pytest.approx(0.0)


def test_run_mean_two_cases() -> None:
    cases = [CASE_HIT, CASE_MISS]
    result = run_benchmark(cases, [PrecisionAtK(k=1)])
    assert result.metric_results[0].mean == pytest.approx(0.5)


def test_run_custom_run_id() -> None:
    result = run_benchmark([CASE_HIT], [ReciprocalRank()], run_id="my-run")
    assert result.run_id == "my-run"


def test_run_default_run_id() -> None:
    result = run_benchmark([CASE_HIT], [ReciprocalRank()])
    assert result.run_id == "default"


def test_run_empty_cases_raises() -> None:
    with pytest.raises(ValueError, match="cases must not be empty"):
        run_benchmark([], [PrecisionAtK(k=1)])


def test_run_empty_metrics_raises() -> None:
    empty: list[Metric] = []
    with pytest.raises(ValueError, match="metrics must not be empty"):
        run_benchmark([CASE_HIT], empty)


def test_run_all_metrics_on_sample_fixture() -> None:
    cases = load_fixture(FIXTURES_DIR / "sample.json")
    metrics: list[Metric] = [
        PrecisionAtK(k=1),
        RecallAtK(k=1),
        TopKAccuracy(k=1),
        ReciprocalRank(),
        NdcgAtK(k=2),
    ]
    result = run_benchmark(cases, metrics, run_id="sample-run")
    assert len(result.metric_results) == 5
    assert result.run_id == "sample-run"
    for mr in result.metric_results:
        assert 0.0 <= mr.mean <= 1.0


def test_run_ndcg_perfect_score() -> None:
    case = _case("c1", ["d1"], frozenset({"d1"}))
    result = run_benchmark([case], [NdcgAtK(k=1)])
    assert result.metric_results[0].mean == pytest.approx(1.0)
