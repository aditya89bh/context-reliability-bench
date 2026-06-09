from __future__ import annotations

from context_reliability_bench.categories.base import BenchmarkCategory
from context_reliability_bench.categories.contradiction import ContradictionCategory
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.runner import run_benchmark
from context_reliability_bench.validation import validate_benchmark_case


def _category() -> ContradictionCategory:
    return ContradictionCategory()


def test_implements_benchmark_category_protocol() -> None:
    assert isinstance(_category(), BenchmarkCategory)


def test_category_name() -> None:
    assert _category().name == "contradiction"


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


def test_each_case_has_exactly_one_relevant_doc() -> None:
    for case in _category().load_cases():
        assert len(case.relevant_doc_ids) == 1


def test_contradictory_docs_present_per_case() -> None:
    for case in _category().load_cases():
        non_relevant = [
            rc for rc in case.context if rc.document.id not in case.relevant_doc_ids
        ]
        # Each contradiction case must have at least one contradictory (wrong) document
        assert len(non_relevant) >= 1


def test_multiple_docs_address_same_query() -> None:
    for case in _category().load_cases():
        # All docs in a contradiction case cover the same topic — so 2+ docs expected
        assert len(case.context) >= 2


def test_not_all_cases_have_relevant_at_rank_1() -> None:
    cases = _category().load_cases()
    at_rank_1 = [
        c
        for c in cases
        if any(
            rc.rank == 1 and rc.document.id in c.relevant_doc_ids
            for rc in c.context
        )
    ]
    # Not every contradiction case should rank the correct doc first
    assert len(at_rank_1) < len(cases)


def test_precision_at_1_below_perfect() -> None:
    cases = _category().load_cases()
    metric = PrecisionAtK(k=1)
    scores = [metric.compute(c.context, c.relevant_doc_ids) for c in cases]
    assert any(s < 1.0 for s in scores)


def test_metrics_run_without_error() -> None:
    metrics: list[Metric] = [PrecisionAtK(k=1), RecallAtK(k=3)]
    result = run_benchmark(_category().load_cases(), metrics)
    assert len(result.metric_results) == 2


def test_run_result_has_correct_case_count() -> None:
    cases = _category().load_cases()
    metrics: list[Metric] = [PrecisionAtK(k=3)]
    result = run_benchmark(cases, metrics)
    assert len(result.metric_results[0].case_scores) == len(cases)
