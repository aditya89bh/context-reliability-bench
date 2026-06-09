from __future__ import annotations

from context_reliability_bench.categories.base import BenchmarkCategory
from context_reliability_bench.categories.temporal_relevance import (
    TemporalRelevanceCategory,
)
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.runner import run_benchmark
from context_reliability_bench.validation import validate_benchmark_case


def _category() -> TemporalRelevanceCategory:
    return TemporalRelevanceCategory()


def test_implements_benchmark_category_protocol() -> None:
    assert isinstance(_category(), BenchmarkCategory)


def test_category_name() -> None:
    assert _category().name == "temporal_relevance"


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


def test_each_case_has_multiple_temporal_documents() -> None:
    for case in _category().load_cases():
        # Temporal cases must have multiple docs spanning different time periods
        assert len(case.context) >= 2


def test_relevant_doc_has_highest_year_in_metadata() -> None:
    for case in _category().load_cases():
        relevant_years = [
            int(rc.document.metadata["year"])
            for rc in case.context
            if rc.document.id in case.relevant_doc_ids
            and "year" in rc.document.metadata
        ]
        all_years = [
            int(rc.document.metadata["year"])
            for rc in case.context
            if "year" in rc.document.metadata
        ]
        if relevant_years and all_years:
            assert max(relevant_years) == max(all_years)


def test_relevant_doc_not_always_at_rank_1() -> None:
    cases = _category().load_cases()
    at_rank_1 = [
        c
        for c in cases
        if any(
            rc.rank == 1 and rc.document.id in c.relevant_doc_ids
            for rc in c.context
        )
    ]
    # Temporal cases should have relevant (newest) doc buried below older docs
    assert len(at_rank_1) < len(cases)


def test_older_docs_ranked_higher_than_newest() -> None:
    for case in _category().load_cases():
        relevant_ranks = [
            rc.rank
            for rc in case.context
            if rc.document.id in case.relevant_doc_ids
        ]
        non_relevant_ranks = [
            rc.rank
            for rc in case.context
            if rc.document.id not in case.relevant_doc_ids
        ]
        if relevant_ranks and non_relevant_ranks:
            # At least one outdated doc should outrank the current doc
            assert min(non_relevant_ranks) < max(relevant_ranks)


def test_metrics_run_without_error() -> None:
    metrics: list[Metric] = [PrecisionAtK(k=1), RecallAtK(k=3)]
    result = run_benchmark(_category().load_cases(), metrics)
    assert len(result.metric_results) == 2


def test_run_result_has_correct_case_count() -> None:
    cases = _category().load_cases()
    metrics: list[Metric] = [PrecisionAtK(k=3)]
    result = run_benchmark(cases, metrics)
    assert len(result.metric_results[0].case_scores) == len(cases)
