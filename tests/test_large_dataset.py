"""Tests that load and execute against the 500-case large_dataset fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

from context_reliability_bench.loader import load_fixture
from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.runner import run_benchmark

_FIXTURE = (
    Path(__file__).parent.parent / "fixtures" / "v1" / "large_dataset.json"
)
_MAX_LOAD_SECONDS = 5.0
_MAX_RUN_SECONDS = 10.0


@pytest.fixture(scope="module")
def large_cases() -> list:  # type: ignore[type-arg]
    return load_fixture(_FIXTURE)


@pytest.fixture(scope="module")
def large_result(large_cases):  # type: ignore[no-untyped-def]
    metrics: list[Metric] = [PrecisionAtK(k=5), RecallAtK(k=5), NdcgAtK(k=5)]
    return run_benchmark(large_cases, metrics, run_id="large-dataset-test")


# ── fixture loading ───────────────────────────────────────────────────────────


def test_large_fixture_loads() -> None:
    cases = load_fixture(_FIXTURE)
    assert len(cases) == 500


def test_large_fixture_all_cases_have_ids() -> None:
    cases = load_fixture(_FIXTURE)
    ids = {c.id for c in cases}
    assert len(ids) == 500


def test_large_fixture_all_cases_have_context(large_cases) -> None:  # type: ignore[no-untyped-def]
    for case in large_cases:
        assert len(case.context) > 0


def test_large_fixture_all_cases_have_relevant_docs(large_cases) -> None:  # type: ignore[no-untyped-def]
    for case in large_cases:
        assert len(case.relevant_doc_ids) > 0


# ── execution ─────────────────────────────────────────────────────────────────


def test_large_dataset_run_id(large_result) -> None:  # type: ignore[no-untyped-def]
    assert large_result.run_id == "large-dataset-test"


def test_large_dataset_metric_count(large_result) -> None:  # type: ignore[no-untyped-def]
    assert len(large_result.metric_results) == 3


def test_large_dataset_case_scores_count(large_result) -> None:  # type: ignore[no-untyped-def]
    for mr in large_result.metric_results:
        assert len(mr.case_scores) == 500


def test_large_dataset_mean_precision_in_range(large_result) -> None:  # type: ignore[no-untyped-def]
    mr = next(r for r in large_result.metric_results if "precision" in r.metric_name)
    assert 0.0 <= mr.mean <= 1.0


def test_large_dataset_mean_recall_in_range(large_result) -> None:  # type: ignore[no-untyped-def]
    mr = next(r for r in large_result.metric_results if "recall" in r.metric_name)
    assert 0.0 <= mr.mean <= 1.0


def test_large_dataset_mean_ndcg_in_range(large_result) -> None:  # type: ignore[no-untyped-def]
    mr = next(r for r in large_result.metric_results if "ndcg" in r.metric_name)
    assert 0.0 <= mr.mean <= 1.0


# ── timing ────────────────────────────────────────────────────────────────────


def test_large_dataset_has_timing(large_result) -> None:  # type: ignore[no-untyped-def]
    assert large_result.timing is not None


def test_large_dataset_within_time_budget(large_result) -> None:  # type: ignore[no-untyped-def]
    """500 cases x 3 metrics must complete within 10 seconds."""
    assert large_result.timing.total_seconds < _MAX_RUN_SECONDS, (
        f"Large benchmark took {large_result.timing.total_seconds:.3f}s "
        f"(limit {_MAX_RUN_SECONDS}s)"
    )


# ── seed determinism on large dataset ────────────────────────────────────────


def test_large_dataset_same_seed_same_order(large_cases) -> None:  # type: ignore[no-untyped-def]
    metrics: list[Metric] = [PrecisionAtK(k=5)]
    r1 = run_benchmark(large_cases, metrics, seed=42)
    r2 = run_benchmark(large_cases, metrics, seed=42)
    ids1 = [cid for cid, _ in r1.metric_results[0].case_scores]
    ids2 = [cid for cid, _ in r2.metric_results[0].case_scores]
    assert ids1 == ids2


def test_large_dataset_seed_mean_unchanged(large_cases) -> None:  # type: ignore[no-untyped-def]
    metrics: list[Metric] = [PrecisionAtK(k=5)]
    r_no = run_benchmark(large_cases, metrics)
    r_seed = run_benchmark(large_cases, metrics, seed=7)
    assert pytest.approx(r_no.metric_results[0].mean) == r_seed.metric_results[0].mean
