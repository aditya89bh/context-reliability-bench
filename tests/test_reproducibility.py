"""Tests for ReproducibilityMetadata and seed-deterministic benchmark runs."""

from __future__ import annotations

import sys

import pytest

from context_reliability_bench import __version__
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.query import Query
from context_reliability_bench.models.retrieved_context import RetrievedContext
from context_reliability_bench.reproducibility import (
    ReproducibilityMetadata,
    capture_metadata,
)
from context_reliability_bench.runner import run_benchmark

# ── helpers ──────────────────────────────────────────────────────────────────


def _rc(doc_id: str, rank: int) -> RetrievedContext:
    return RetrievedContext(
        document=Document(id=doc_id, content=f"Content of {doc_id}"),
        score=1.0 - rank * 0.05,
        rank=rank,
    )


def _case(case_id: str, doc_ids: list[str], relevant: frozenset[str]) -> BenchmarkCase:
    return BenchmarkCase(
        id=case_id,
        query=Query(id=f"q-{case_id}", text="test query"),
        context=tuple(_rc(d, i + 1) for i, d in enumerate(doc_ids)),
        relevant_doc_ids=relevant,
        expected_answer="answer",
    )


_CASES = [
    _case(f"c{i}", [f"d{i}a", f"d{i}b"], frozenset({f"d{i}a"}))
    for i in range(6)
]
_METRICS: list[Metric] = [PrecisionAtK(k=3)]


# ── ReproducibilityMetadata ───────────────────────────────────────────────────


def test_capture_metadata_python_version() -> None:
    meta = capture_metadata()
    assert sys.version in meta.python_version


def test_capture_metadata_library_version() -> None:
    meta = capture_metadata()
    assert meta.library_version == __version__


def test_capture_metadata_platform_populated() -> None:
    meta = capture_metadata()
    assert meta.platform_system != ""
    assert meta.platform_machine != ""


def test_capture_metadata_seed_none_by_default() -> None:
    meta = capture_metadata()
    assert meta.seed is None


def test_capture_metadata_seed_stored() -> None:
    meta = capture_metadata(seed=42)
    assert meta.seed == 42


def test_is_reproducible_without_seed() -> None:
    meta = capture_metadata()
    assert not meta.is_reproducible()


def test_is_reproducible_with_seed() -> None:
    meta = capture_metadata(seed=0)
    assert meta.is_reproducible()


def test_as_dict_contains_all_keys() -> None:
    meta = capture_metadata(seed=7)
    d = meta.as_dict()
    for key in ("python_version", "platform_system", "platform_machine",
                "library_version", "seed"):
        assert key in d


def test_as_dict_seed_value() -> None:
    meta = capture_metadata(seed=99)
    assert meta.as_dict()["seed"] == 99


def test_metadata_frozen() -> None:
    import dataclasses
    meta = capture_metadata(seed=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        meta.seed = 2  # type: ignore[misc]


# ── RunResult seed field ──────────────────────────────────────────────────────


def test_run_result_seed_none_by_default() -> None:
    result = run_benchmark(_CASES, _METRICS, run_id="r")
    assert result.seed is None


def test_run_result_seed_stored() -> None:
    result = run_benchmark(_CASES, _METRICS, run_id="r", seed=42)
    assert result.seed == 42


# ── Deterministic ordering ────────────────────────────────────────────────────


def test_same_seed_produces_same_case_order() -> None:
    r1 = run_benchmark(_CASES, _METRICS, run_id="r", seed=17)
    r2 = run_benchmark(_CASES, _METRICS, run_id="r", seed=17)
    ids1 = [cid for cid, _ in r1.metric_results[0].case_scores]
    ids2 = [cid for cid, _ in r2.metric_results[0].case_scores]
    assert ids1 == ids2


def test_different_seeds_produce_different_case_orders() -> None:
    # With 6 cases the probability that two random permutations are identical
    # is 1/720, which is negligible for a unit test.
    r1 = run_benchmark(_CASES, _METRICS, run_id="r", seed=1)
    r2 = run_benchmark(_CASES, _METRICS, run_id="r", seed=2)
    ids1 = [cid for cid, _ in r1.metric_results[0].case_scores]
    ids2 = [cid for cid, _ in r2.metric_results[0].case_scores]
    assert ids1 != ids2


def test_seed_does_not_change_mean_score() -> None:
    r_no_seed = run_benchmark(_CASES, _METRICS, run_id="r")
    r_seed = run_benchmark(_CASES, _METRICS, run_id="r", seed=42)
    assert pytest.approx(r_no_seed.metric_results[0].mean) == (
        r_seed.metric_results[0].mean
    )


def test_no_seed_preserves_fixture_order() -> None:
    result = run_benchmark(_CASES, _METRICS, run_id="r")
    original_ids = [c.id for c in _CASES]
    result_ids = [cid for cid, _ in result.metric_results[0].case_scores]
    assert result_ids == original_ids


# ── RunResult reproducibility field ──────────────────────────────────────────


def test_run_result_reproducibility_none_by_default() -> None:
    result = run_benchmark(_CASES, _METRICS, run_id="r")
    assert result.reproducibility is None


def test_run_result_accepts_reproducibility_metadata() -> None:
    meta = capture_metadata(seed=5)
    result = run_benchmark(_CASES, _METRICS, run_id="r", seed=5)
    from context_reliability_bench.models.run_result import RunResult
    result_with_meta = RunResult(
        run_id=result.run_id,
        metric_results=result.metric_results,
        seed=result.seed,
        reproducibility=meta,
    )
    assert result_with_meta.reproducibility is meta
    assert result_with_meta.reproducibility.seed == 5


def test_reproducibility_metadata_on_run_result_is_accessible() -> None:
    meta = capture_metadata(seed=3)
    from context_reliability_bench.models.run_result import RunResult
    result = RunResult(
        run_id="test",
        metric_results=(),
        seed=3,
        reproducibility=meta,
    )
    assert isinstance(result.reproducibility, ReproducibilityMetadata)
    assert result.reproducibility.is_reproducible()
