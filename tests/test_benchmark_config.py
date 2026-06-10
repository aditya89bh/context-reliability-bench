from __future__ import annotations

import dataclasses

from context_reliability_bench.config.model import (
    _DEFAULT_METRICS,
    BenchmarkConfig,
    ConfigError,
)


def test_required_fixture_path() -> None:
    cfg = BenchmarkConfig(fixture_path="fixtures/sample.json")
    assert cfg.fixture_path == "fixtures/sample.json"


def test_defaults() -> None:
    cfg = BenchmarkConfig(fixture_path="f.json")
    assert cfg.run_id == "default"
    assert cfg.k == 5
    assert cfg.metric_names == _DEFAULT_METRICS
    assert cfg.output_json is None
    assert cfg.output_csv is None
    assert cfg.tags == frozenset()


def test_custom_values() -> None:
    cfg = BenchmarkConfig(
        fixture_path="f.json",
        run_id="ci-run",
        k=10,
        metric_names=("precision", "recall"),
        output_json="out.json",
        output_csv="out.csv",
        tags=frozenset({"nightly", "ci"}),
    )
    assert cfg.run_id == "ci-run"
    assert cfg.k == 10
    assert cfg.metric_names == ("precision", "recall")
    assert cfg.output_json == "out.json"
    assert cfg.output_csv == "out.csv"
    assert "nightly" in cfg.tags


def test_frozen() -> None:
    cfg = BenchmarkConfig(fixture_path="f.json")
    try:
        cfg.k = 99  # type: ignore[misc]
        raise AssertionError("should have raised FrozenInstanceError")
    except dataclasses.FrozenInstanceError:
        pass


def test_default_metrics_tuple() -> None:
    assert isinstance(_DEFAULT_METRICS, tuple)
    assert "precision" in _DEFAULT_METRICS


def test_config_error_is_exception() -> None:
    err = ConfigError("bad config")
    assert isinstance(err, Exception)
    assert str(err) == "bad config"


def test_tags_independent_across_instances() -> None:
    cfg1 = BenchmarkConfig(fixture_path="f.json")
    cfg2 = BenchmarkConfig(fixture_path="g.json")
    assert cfg1.tags is not cfg2.tags
    assert cfg1.tags == cfg2.tags == frozenset()
