from __future__ import annotations

from context_reliability_bench.categories.base import BenchmarkCategory
from context_reliability_bench.categories.noise_resistance import (
    NoiseResistanceCategory,
)
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.runner import run_benchmark
from context_reliability_bench.validation import validate_benchmark_case


def _category() -> NoiseResistanceCategory:
    return NoiseResistanceCategory()


def test_implements_benchmark_category_protocol() -> None:
    assert isinstance(_category(), BenchmarkCategory)


def test_category_name() -> None:
    assert _category().name == "noise_resistance"


def test_category_version() -> None:
    assert _category().version == "1.0"


def test_category_description_nonempty() -> None:
    assert len(_category().description) > 0


def test_cases_load_returns_list() -> None:
    cases = _category().load_cases()
    assert isinstance(cases, list)


def test_cases_count_at_least_three() -> None:
    assert len(_category().load_cases()) >= 3


def test_all_cases_pass_validation() -> None:
    for case in _category().load_cases():
        validate_benchmark_case(case)


def test_all_cases_have_nonempty_ids() -> None:
    for case in _category().load_cases():
        assert case.id
        assert case.query.id
        assert case.query.text


def test_all_cases_have_expected_answer() -> None:
    for case in _category().load_cases():
        assert case.expected_answer


def test_relevant_doc_not_at_rank_1_for_all_cases() -> None:
    cases = _category().load_cases()
    rank_1_relevant = [
        case
        for case in cases
        if any(
            rc.rank == 1 and rc.document.id in case.relevant_doc_ids
            for rc in case.context
        )
    ]
    # Noise resistance: at least one case must have the relevant doc buried past rank 1
    assert len(rank_1_relevant) < len(cases)


def test_noise_docs_have_higher_scores_than_relevant() -> None:
    for case in _category().load_cases():
        relevant_scores = [
            rc.score
            for rc in case.context
            if rc.document.id in case.relevant_doc_ids
        ]
        noise_scores = [
            rc.score
            for rc in case.context
            if rc.document.id not in case.relevant_doc_ids
        ]
        if relevant_scores and noise_scores:
            # At least one noise doc should score higher than the relevant doc
            assert max(noise_scores) > min(relevant_scores)


def test_precision_at_1_below_1_for_most_cases() -> None:
    cases = _category().load_cases()
    metric = PrecisionAtK(k=1)
    scores = [metric.compute(c.context, c.relevant_doc_ids) for c in cases]
    # Noise at top means P@1 < 1.0 for at least one case
    assert any(s < 1.0 for s in scores)


def test_recall_at_k_higher_than_precision_at_1() -> None:
    cases = _category().load_cases()
    k = max(len(c.context) for c in cases)
    p1 = PrecisionAtK(k=1)
    recall = RecallAtK(k=k)
    for case in cases:
        p_score = p1.compute(case.context, case.relevant_doc_ids)
        r_score = recall.compute(case.context, case.relevant_doc_ids)
        # Recall at full depth must be >= precision@1
        assert r_score >= p_score


def test_metrics_run_without_error() -> None:
    metrics: list[Metric] = [PrecisionAtK(k=1), RecallAtK(k=3)]
    result = run_benchmark(_category().load_cases(), metrics)
    assert len(result.metric_results) == 2


def test_run_result_has_correct_case_count() -> None:
    cases = _category().load_cases()
    metrics: list[Metric] = [PrecisionAtK(k=1)]
    result = run_benchmark(cases, metrics)
    mr = result.metric_results[0]
    assert len(mr.case_scores) == len(cases)
