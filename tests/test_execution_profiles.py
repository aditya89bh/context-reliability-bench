from __future__ import annotations

from context_reliability_bench.config.profiles import (
    ExecutionProfile,
    config_from_profile,
)


def test_quick_k() -> None:
    cfg = config_from_profile("f.json", ExecutionProfile.QUICK)
    assert cfg.k == 3


def test_standard_k() -> None:
    cfg = config_from_profile("f.json", ExecutionProfile.STANDARD)
    assert cfg.k == 5


def test_thorough_k() -> None:
    cfg = config_from_profile("f.json", ExecutionProfile.THOROUGH)
    assert cfg.k == 10


def test_quick_has_two_metrics() -> None:
    cfg = config_from_profile("f.json", ExecutionProfile.QUICK)
    assert cfg.metric_names == ("precision", "recall")


def test_standard_has_five_metrics() -> None:
    cfg = config_from_profile("f.json", ExecutionProfile.STANDARD)
    assert len(cfg.metric_names) == 5


def test_thorough_has_five_metrics() -> None:
    cfg = config_from_profile("f.json", ExecutionProfile.THOROUGH)
    assert len(cfg.metric_names) == 5


def test_fixture_path_passed_through() -> None:
    cfg = config_from_profile("my/fixture.json", ExecutionProfile.STANDARD)
    assert cfg.fixture_path == "my/fixture.json"


def test_run_id_passed_through() -> None:
    cfg = config_from_profile("f.json", ExecutionProfile.STANDARD, run_id="run-42")
    assert cfg.run_id == "run-42"


def test_default_run_id() -> None:
    cfg = config_from_profile("f.json", ExecutionProfile.QUICK)
    assert cfg.run_id == "default"


def test_tags_passed_through() -> None:
    tags = frozenset({"ci", "nightly"})
    cfg = config_from_profile("f.json", ExecutionProfile.STANDARD, tags=tags)
    assert cfg.tags == tags


def test_default_tags_empty() -> None:
    cfg = config_from_profile("f.json", ExecutionProfile.QUICK)
    assert cfg.tags == frozenset()


def test_profile_enum_values() -> None:
    assert ExecutionProfile.QUICK.value == "quick"
    assert ExecutionProfile.STANDARD.value == "standard"
    assert ExecutionProfile.THOROUGH.value == "thorough"
