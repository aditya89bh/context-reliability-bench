from __future__ import annotations

from pathlib import Path

import pytest

from context_reliability_bench.batch import BatchError, BatchResult, run_batch
from context_reliability_bench.config.model import BenchmarkConfig

_SAMPLE = str(Path(__file__).parent.parent / "fixtures" / "sample.json")


def _cfg(run_id: str = "r", fixture: str = _SAMPLE) -> BenchmarkConfig:
    return BenchmarkConfig(
        fixture_path=fixture,
        run_id=run_id,
        k=3,
        metric_names=("precision", "recall"),
    )


def test_single_config_returns_one_result() -> None:
    result = run_batch([_cfg()])
    assert len(result.results) == 1


def test_run_id_preserved() -> None:
    result = run_batch([_cfg(run_id="my-run")])
    assert result.results[0].run_id == "my-run"


def test_multiple_configs() -> None:
    result = run_batch([_cfg("r1"), _cfg("r2")])
    assert len(result.results) == 2


def test_get_by_run_id_found() -> None:
    result = run_batch([_cfg("alpha")])
    run = result.get_by_run_id("alpha")
    assert run is not None
    assert run.run_id == "alpha"


def test_get_by_run_id_not_found() -> None:
    result = run_batch([_cfg("alpha")])
    assert result.get_by_run_id("beta") is None


def test_all_passed_true() -> None:
    result = run_batch([_cfg()])
    assert result.all_passed(0.0) is True


def test_all_passed_false_for_high_threshold() -> None:
    result = run_batch([_cfg()])
    assert result.all_passed(2.0) is False


def test_empty_configs_raises() -> None:
    with pytest.raises(ValueError, match="configs"):
        run_batch([])


def test_bad_fixture_raises_batch_error() -> None:
    cfg = BenchmarkConfig(fixture_path="nonexistent/path.json", run_id="r")
    with pytest.raises(BatchError, match="Failed to load"):
        run_batch([cfg])


def test_unknown_metric_name_falls_back_to_precision() -> None:
    cfg = BenchmarkConfig(
        fixture_path=_SAMPLE,
        run_id="r",
        metric_names=("unknown_metric",),
    )
    result = run_batch([cfg])
    assert result.results[0].metric_results[0].metric_name.startswith("precision")


def test_batch_result_is_frozen() -> None:
    result = BatchResult(results=())
    import dataclasses

    try:
        result.results = ()  # type: ignore[misc]
        raise AssertionError("should have raised FrozenInstanceError")
    except dataclasses.FrozenInstanceError:
        pass
