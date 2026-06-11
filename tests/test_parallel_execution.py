"""Tests that parallel execution produces results equivalent to sequential."""

from __future__ import annotations

from pathlib import Path

import pytest

from context_reliability_bench.batch import run_batch
from context_reliability_bench.config.model import BenchmarkConfig
from context_reliability_bench.parallel import run_parallel

_FIXTURE = str(Path(__file__).parent.parent / "fixtures" / "sample.json")
_FIXTURE_NOISE = str(
    Path(__file__).parent.parent / "fixtures" / "v1" / "noise_resistance.json"
)
_FIXTURE_CONTRA = str(
    Path(__file__).parent.parent / "fixtures" / "v1" / "contradiction.json"
)


def _cfg(
    run_id: str, fixture: str = _FIXTURE, seed: int | None = None
) -> BenchmarkConfig:
    return BenchmarkConfig(
        fixture_path=fixture,
        run_id=run_id,
        k=5,
        metric_names=("precision", "recall", "ndcg"),
        seed=seed,
    )


# ── basic parallel execution ──────────────────────────────────────────────────


def test_parallel_empty_returns_empty() -> None:
    assert run_parallel([]) == []


def test_parallel_single_config_returns_one_result() -> None:
    results = run_parallel([_cfg("r1")])
    assert len(results) == 1


def test_parallel_single_run_id() -> None:
    results = run_parallel([_cfg("my-run")])
    assert results[0].run_id == "my-run"


def test_parallel_multiple_configs_count() -> None:
    cfgs = [_cfg(f"r{i}") for i in range(4)]
    results = run_parallel(cfgs)
    assert len(results) == 4


# ── ordering guarantee ────────────────────────────────────────────────────────


def test_parallel_results_in_input_order() -> None:
    """Results must match the order of configs, not completion order."""
    cfgs = [
        _cfg("first", fixture=_FIXTURE_NOISE),
        _cfg("second", fixture=_FIXTURE_CONTRA),
        _cfg("third", fixture=_FIXTURE),
    ]
    results = run_parallel(cfgs)
    assert [r.run_id for r in results] == ["first", "second", "third"]


def test_parallel_order_stable_across_runs() -> None:
    cfgs = [_cfg(f"run-{i}", seed=i) for i in range(5)]
    r1 = run_parallel(cfgs)
    r2 = run_parallel(cfgs)
    assert [r.run_id for r in r1] == [r.run_id for r in r2]


# ── equivalence with sequential execution ─────────────────────────────────────


def test_parallel_mean_equals_sequential() -> None:
    """Parallel and sequential runs on the same fixture must return the same mean."""
    cfg = _cfg("equiv", seed=42)

    sequential = run_batch([cfg]).results[0]
    parallel_results = run_parallel([cfg])

    for par_mr in parallel_results[0].metric_results:
        seq_mr = next(
            mr for mr in sequential.metric_results
            if mr.metric_name == par_mr.metric_name
        )
        assert pytest.approx(par_mr.mean) == seq_mr.mean, (
            f"Divergence on {par_mr.metric_name}: "
            f"parallel={par_mr.mean:.4f} sequential={seq_mr.mean:.4f}"
        )


def test_parallel_multi_config_means_match_sequential() -> None:
    cfgs = [
        _cfg("a", fixture=_FIXTURE, seed=1),
        _cfg("b", fixture=_FIXTURE_NOISE, seed=2),
        _cfg("c", fixture=_FIXTURE_CONTRA, seed=3),
    ]
    seq_results = run_batch(cfgs).results
    par_results = run_parallel(cfgs)

    for seq, par in zip(seq_results, par_results, strict=True):
        assert seq.run_id == par.run_id
        for seq_mr in seq.metric_results:
            par_mr = next(
                mr for mr in par.metric_results
                if mr.metric_name == seq_mr.metric_name
            )
            assert pytest.approx(seq_mr.mean) == par_mr.mean


# ── seed propagation ─────────────────────────────────────────────────────────


def test_parallel_seed_is_stored_in_result() -> None:
    results = run_parallel([_cfg("seeded", seed=77)])
    assert results[0].seed == 77


def test_parallel_no_seed_stored_as_none() -> None:
    results = run_parallel([_cfg("unseeded")])
    assert results[0].seed is None


def test_parallel_seed_produces_deterministic_case_order() -> None:
    cfg = _cfg("det", seed=13)
    r1 = run_parallel([cfg])[0]
    r2 = run_parallel([cfg])[0]
    ids1 = [cid for cid, _ in r1.metric_results[0].case_scores]
    ids2 = [cid for cid, _ in r2.metric_results[0].case_scores]
    assert ids1 == ids2


# ── max_workers parameter ─────────────────────────────────────────────────────


def test_parallel_single_worker_still_correct() -> None:
    cfgs = [_cfg(f"w{i}", seed=i) for i in range(3)]
    r_single = run_parallel(cfgs, max_workers=1)
    r_multi = run_parallel(cfgs)
    for s, m in zip(r_single, r_multi, strict=True):
        assert s.run_id == m.run_id
        for smr, mmr in zip(s.metric_results, m.metric_results, strict=True):
            assert pytest.approx(smr.mean) == mmr.mean
