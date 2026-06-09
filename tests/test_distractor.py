from __future__ import annotations

from context_reliability_bench.categories.base import BenchmarkCategory
from context_reliability_bench.categories.distractor import DistractorCategory
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.runner import run_benchmark
from context_reliability_bench.validation import validate_benchmark_case


def _category() -> DistractorCategory:
    return DistractorCategory()


def test_implements_benchmark_category_protocol() -> None:
    assert isinstance(_category(), BenchmarkCategory)


def test_category_name() -> None:
    assert _category().name == "distractor"


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


def test_distractor_docs_outnumber_relevant() -> None:
    for case in _category().load_cases():
        n_distractor = sum(
            1
            for rc in case.context
            if rc.document.id not in case.relevant_doc_ids
        )
        assert n_distractor >= 2


def test_relevant_doc_not_at_rank_1_for_all_cases() -> None:
    cases = _category().load_cases()
    at_rank_1 = [
        c
        for c in cases
        if any(
            rc.rank == 1 and rc.document.id in c.relevant_doc_ids
            for rc in c.context
        )
    ]
    # Distractor cases: distractors dominate top ranks
    assert len(at_rank_1) < len(cases)


def test_distractors_score_higher_than_relevant() -> None:
    for case in _category().load_cases():
        relevant_scores = [
            rc.score
            for rc in case.context
            if rc.document.id in case.relevant_doc_ids
        ]
        distractor_scores = [
            rc.score
            for rc in case.context
            if rc.document.id not in case.relevant_doc_ids
        ]
        if relevant_scores and distractor_scores:
            assert max(distractor_scores) > max(relevant_scores)


def test_precision_at_1_is_zero_for_all_cases() -> None:
    metric = PrecisionAtK(k=1)
    for case in _category().load_cases():
        score = metric.compute(case.context, case.relevant_doc_ids)
        assert score == 0.0


def test_recall_at_full_depth_is_one_for_all_cases() -> None:
    for case in _category().load_cases():
        k = len(case.context)
        metric = RecallAtK(k=k)
        score = metric.compute(case.context, case.relevant_doc_ids)
        assert score == 1.0


def test_metrics_run_without_error() -> None:
    metrics: list[Metric] = [PrecisionAtK(k=1), RecallAtK(k=4)]
    result = run_benchmark(_category().load_cases(), metrics)
    assert len(result.metric_results) == 2


def test_run_result_has_correct_case_count() -> None:
    cases = _category().load_cases()
    metrics: list[Metric] = [PrecisionAtK(k=4)]
    result = run_benchmark(cases, metrics)
    assert len(result.metric_results[0].case_scores) == len(cases)
