from __future__ import annotations

import math

import pytest

from context_reliability_bench.metrics.mrr import ReciprocalRank
from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.metrics.top_k_accuracy import TopKAccuracy
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.retrieved_context import RetrievedContext


def _rc(doc_id: str, rank: int, score: float = 0.9) -> RetrievedContext:
    return RetrievedContext(
        document=Document(id=doc_id, content=f"Content of {doc_id}."),
        score=score,
        rank=rank,
    )


RETRIEVED: tuple[RetrievedContext, ...] = (
    _rc("d1", rank=1, score=0.9),
    _rc("d2", rank=2, score=0.8),
    _rc("d3", rank=3, score=0.7),
    _rc("d4", rank=4, score=0.6),
    _rc("d5", rank=5, score=0.5),
)

REL_FIRST = frozenset({"d1"})
REL_LAST = frozenset({"d5"})
REL_NONE = frozenset({"d99"})
REL_ALL = frozenset({"d1", "d2", "d3", "d4", "d5"})
REL_ODD = frozenset({"d1", "d3", "d5"})


# ---------------------------------------------------------------------------
# PrecisionAtK
# ---------------------------------------------------------------------------


def test_precision_name() -> None:
    assert PrecisionAtK(k=3).name == "precision@3"


def test_precision_invalid_k() -> None:
    with pytest.raises(ValueError):
        PrecisionAtK(k=0)


def test_precision_at_1_hit() -> None:
    assert PrecisionAtK(k=1).compute(RETRIEVED, REL_FIRST) == pytest.approx(1.0)


def test_precision_at_1_miss() -> None:
    assert PrecisionAtK(k=1).compute(RETRIEVED, REL_LAST) == pytest.approx(0.0)


def test_precision_at_3_partial() -> None:
    # d1 and d3 relevant in top-3 → 2/3
    rel = frozenset({"d1", "d3"})
    assert PrecisionAtK(k=3).compute(RETRIEVED, rel) == pytest.approx(2 / 3)


def test_precision_at_5_all() -> None:
    assert PrecisionAtK(k=5).compute(RETRIEVED, REL_ALL) == pytest.approx(1.0)


def test_precision_at_5_none() -> None:
    assert PrecisionAtK(k=5).compute(RETRIEVED, REL_NONE) == pytest.approx(0.0)


def test_precision_k_larger_than_retrieved() -> None:
    # k=10 but only 5 docs — denominator is k
    assert PrecisionAtK(k=10).compute(RETRIEVED, REL_FIRST) == pytest.approx(1 / 10)


# ---------------------------------------------------------------------------
# RecallAtK
# ---------------------------------------------------------------------------


def test_recall_name() -> None:
    assert RecallAtK(k=5).name == "recall@5"


def test_recall_invalid_k() -> None:
    with pytest.raises(ValueError):
        RecallAtK(k=0)


def test_recall_at_1_full() -> None:
    # only 1 relevant, retrieved at rank 1 → 1/1
    assert RecallAtK(k=1).compute(RETRIEVED, REL_FIRST) == pytest.approx(1.0)


def test_recall_at_1_miss() -> None:
    # relevant is d5, not in top-1 → 0/1
    assert RecallAtK(k=1).compute(RETRIEVED, REL_LAST) == pytest.approx(0.0)


def test_recall_at_5_last() -> None:
    # d5 retrieved at rank 5, 1 relevant → 1/1
    assert RecallAtK(k=5).compute(RETRIEVED, REL_LAST) == pytest.approx(1.0)


def test_recall_at_3_partial() -> None:
    # d1, d3, d5 relevant; top-3 finds d1 and d3 → 2/3
    assert RecallAtK(k=3).compute(RETRIEVED, REL_ODD) == pytest.approx(2 / 3)


def test_recall_at_5_all() -> None:
    assert RecallAtK(k=5).compute(RETRIEVED, REL_ALL) == pytest.approx(1.0)


def test_recall_empty_relevant() -> None:
    assert RecallAtK(k=5).compute(RETRIEVED, frozenset()) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# TopKAccuracy
# ---------------------------------------------------------------------------


def test_topk_name() -> None:
    assert TopKAccuracy(k=3).name == "top3_accuracy"


def test_topk_invalid_k() -> None:
    with pytest.raises(ValueError):
        TopKAccuracy(k=0)


def test_topk_at_1_hit() -> None:
    assert TopKAccuracy(k=1).compute(RETRIEVED, REL_FIRST) == pytest.approx(1.0)


def test_topk_at_1_miss() -> None:
    assert TopKAccuracy(k=1).compute(RETRIEVED, REL_LAST) == pytest.approx(0.0)


def test_topk_at_5_last() -> None:
    assert TopKAccuracy(k=5).compute(RETRIEVED, REL_LAST) == pytest.approx(1.0)


def test_topk_at_5_none() -> None:
    assert TopKAccuracy(k=5).compute(RETRIEVED, REL_NONE) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# ReciprocalRank (MRR per case)
# ---------------------------------------------------------------------------


def test_rr_name() -> None:
    assert ReciprocalRank().name == "reciprocal_rank"


def test_rr_first_rank() -> None:
    assert ReciprocalRank().compute(RETRIEVED, REL_FIRST) == pytest.approx(1.0)


def test_rr_second_rank() -> None:
    assert ReciprocalRank().compute(RETRIEVED, frozenset({"d2"})) == pytest.approx(0.5)


def test_rr_fifth_rank() -> None:
    assert ReciprocalRank().compute(RETRIEVED, REL_LAST) == pytest.approx(0.2)


def test_rr_not_retrieved() -> None:
    assert ReciprocalRank().compute(RETRIEVED, REL_NONE) == pytest.approx(0.0)


def test_rr_empty_retrieved() -> None:
    assert ReciprocalRank().compute((), REL_FIRST) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# NdcgAtK
# ---------------------------------------------------------------------------


def test_ndcg_name() -> None:
    assert NdcgAtK(k=5).name == "ndcg@5"


def test_ndcg_invalid_k() -> None:
    with pytest.raises(ValueError):
        NdcgAtK(k=0)


def test_ndcg_perfect_rank_1() -> None:
    # Single relevant doc at rank 1 → nDCG = 1.0
    assert NdcgAtK(k=1).compute(RETRIEVED, REL_FIRST) == pytest.approx(1.0)


def test_ndcg_none_relevant_in_top_k() -> None:
    assert NdcgAtK(k=5).compute(RETRIEVED, REL_NONE) == pytest.approx(0.0)


def test_ndcg_all_relevant_perfect_order() -> None:
    # All 5 docs relevant in order → DCG = IDCG → nDCG = 1.0
    assert NdcgAtK(k=5).compute(RETRIEVED, REL_ALL) == pytest.approx(1.0)


def test_ndcg_partial_at_3() -> None:
    # d1 (rank 1) and d3 (rank 3) relevant, k=3
    # DCG@3 = 1/log2(2) + 1/log2(4) = 1.0 + 0.5 = 1.5
    # IDCG@3 (2 relevant) = 1/log2(2) + 1/log2(3)
    relevant = frozenset({"d1", "d3"})
    dcg = 1.0 / math.log2(2) + 1.0 / math.log2(4)
    idcg = 1.0 / math.log2(2) + 1.0 / math.log2(3)
    expected = dcg / idcg
    assert NdcgAtK(k=3).compute(RETRIEVED, relevant) == pytest.approx(expected)


def test_ndcg_relevant_below_k_cutoff() -> None:
    # d5 relevant, k=3 — not in top-3 → nDCG = 0.0
    assert NdcgAtK(k=3).compute(RETRIEVED, REL_LAST) == pytest.approx(0.0)
