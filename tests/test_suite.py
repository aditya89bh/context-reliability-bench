from __future__ import annotations

import pytest

from context_reliability_bench.categories.noise_resistance import (
    NoiseResistanceCategory,
)
from context_reliability_bench.categories.registry import CategoryRegistry
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.suite import (
    SuiteResult,
    build_default_registry,
    run_suite,
)


def test_build_default_registry_has_four_categories() -> None:
    assert len(build_default_registry()) == 4


def test_build_default_registry_contains_all_names() -> None:
    names = set(build_default_registry().names())
    assert names == {
        "noise_resistance",
        "contradiction",
        "temporal_relevance",
        "distractor",
    }


def test_build_default_registry_names_sorted() -> None:
    names = build_default_registry().names()
    assert names == sorted(names)


def test_run_suite_returns_suite_result() -> None:
    registry = build_default_registry()
    metrics: list[Metric] = [PrecisionAtK(k=1)]
    result = run_suite(registry, metrics)
    assert isinstance(result, SuiteResult)


def test_run_suite_covers_all_categories() -> None:
    registry = build_default_registry()
    metrics: list[Metric] = [PrecisionAtK(k=1)]
    result = run_suite(registry, metrics)
    assert set(result.names()) == {
        "noise_resistance",
        "contradiction",
        "temporal_relevance",
        "distractor",
    }


def test_run_suite_get_known_category() -> None:
    registry = build_default_registry()
    metrics: list[Metric] = [PrecisionAtK(k=1)]
    result = run_suite(registry, metrics)
    run = result.get("noise_resistance")
    assert run is not None
    assert run.run_id == "noise_resistance"


def test_run_suite_get_missing_returns_none() -> None:
    registry = build_default_registry()
    metrics: list[Metric] = [PrecisionAtK(k=1)]
    result = run_suite(registry, metrics)
    assert result.get("nonexistent") is None


def test_run_suite_metric_results_present() -> None:
    registry = build_default_registry()
    metrics: list[Metric] = [PrecisionAtK(k=1)]
    result = run_suite(registry, metrics)
    for name in result.names():
        run = result.get(name)
        assert run is not None
        assert len(run.metric_results) == 1


def test_run_suite_multiple_metrics() -> None:
    registry = build_default_registry()
    metrics: list[Metric] = [PrecisionAtK(k=1), PrecisionAtK(k=3)]
    result = run_suite(registry, metrics)
    for name in result.names():
        run = result.get(name)
        assert run is not None
        assert len(run.metric_results) == 2


def test_run_suite_empty_metrics_raises() -> None:
    registry = build_default_registry()
    empty: list[Metric] = []
    with pytest.raises(ValueError, match="metrics must not be empty"):
        run_suite(registry, empty)


def test_run_suite_empty_registry_returns_empty_result() -> None:
    registry = CategoryRegistry()
    metrics: list[Metric] = [PrecisionAtK(k=1)]
    result = run_suite(registry, metrics)
    assert result.names() == []
    assert result.category_results == ()


def test_registry_register_duplicate_raises() -> None:
    registry = CategoryRegistry()
    cat = NoiseResistanceCategory()
    registry.register(cat)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(cat)


def test_registry_get_known_category() -> None:
    registry = build_default_registry()
    cat = registry.get("distractor")
    assert cat.name == "distractor"


def test_registry_get_unknown_raises() -> None:
    registry = CategoryRegistry()
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_registry_contains_operator() -> None:
    registry = build_default_registry()
    assert "noise_resistance" in registry
    assert "unknown" not in registry


def test_suite_result_names_order_matches_sorted_registry() -> None:
    registry = build_default_registry()
    metrics: list[Metric] = [PrecisionAtK(k=1)]
    result = run_suite(registry, metrics)
    assert result.names() == sorted(result.names())
