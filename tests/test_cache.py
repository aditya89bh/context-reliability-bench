"""Tests for BenchmarkCache: correctness, invalidation, and corrupt entries."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from context_reliability_bench.cache import (
    BenchmarkCache,
    CacheError,
    make_cache_key,
    make_retriever_cache_key,
)
from context_reliability_bench.config.model import BenchmarkConfig
from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult

_FIXTURE = str(Path(__file__).parent.parent / "fixtures" / "sample.json")
_FIXTURE_NOISE = str(
    Path(__file__).parent.parent / "fixtures" / "v1" / "noise_resistance.json"
)


def _cfg(run_id: str = "test", seed: int | None = None) -> BenchmarkConfig:
    return BenchmarkConfig(
        fixture_path=_FIXTURE,
        run_id=run_id,
        k=5,
        metric_names=("precision", "recall"),
        seed=seed,
    )


def _result(run_id: str = "test") -> RunResult:
    return RunResult(
        run_id=run_id,
        metric_results=(
            MetricResult(
                metric_name="precision@5",
                case_scores=(("c1", 1.0), ("c2", 0.5)),
                mean=0.75,
            ),
        ),
        seed=None,
    )


# ── CacheKey ──────────────────────────────────────────────────────────────────


def test_cache_key_digest_is_string() -> None:
    key = make_cache_key(_cfg())
    assert isinstance(key.digest(), str)
    assert len(key.digest()) == 64  # SHA-256 hex


def test_cache_key_same_config_same_digest() -> None:
    k1 = make_cache_key(_cfg(run_id="r", seed=1))
    k2 = make_cache_key(_cfg(run_id="r", seed=1))
    assert k1.digest() == k2.digest()


def test_cache_key_different_run_id_different_digest() -> None:
    k1 = make_cache_key(_cfg(run_id="a"))
    k2 = make_cache_key(_cfg(run_id="b"))
    assert k1.digest() != k2.digest()


def test_cache_key_different_seed_different_digest() -> None:
    k1 = make_cache_key(_cfg(seed=1))
    k2 = make_cache_key(_cfg(seed=2))
    assert k1.digest() != k2.digest()


def test_cache_key_different_fixture_different_digest() -> None:
    cfg_a = BenchmarkConfig(fixture_path=_FIXTURE, run_id="r", k=5,
                            metric_names=("precision",))
    cfg_b = BenchmarkConfig(fixture_path=_FIXTURE_NOISE, run_id="r", k=5,
                            metric_names=("precision",))
    k1 = make_cache_key(cfg_a)
    k2 = make_cache_key(cfg_b)
    assert k1.digest() != k2.digest()


def test_cache_key_different_metrics_different_digest() -> None:
    cfg_a = BenchmarkConfig(fixture_path=_FIXTURE, run_id="r", k=5,
                            metric_names=("precision",))
    cfg_b = BenchmarkConfig(fixture_path=_FIXTURE, run_id="r", k=5,
                            metric_names=("recall",))
    k1 = make_cache_key(cfg_a)
    k2 = make_cache_key(cfg_b)
    assert k1.digest() != k2.digest()


def test_cache_key_different_k_different_digest() -> None:
    cfg_a = BenchmarkConfig(fixture_path=_FIXTURE, run_id="r", k=5,
                            metric_names=("precision",))
    cfg_b = BenchmarkConfig(fixture_path=_FIXTURE, run_id="r", k=10,
                            metric_names=("precision",))
    k1 = make_cache_key(cfg_a)
    k2 = make_cache_key(cfg_b)
    assert k1.digest() != k2.digest()


def test_cache_key_is_frozen() -> None:
    key = make_cache_key(_cfg())
    with pytest.raises(dataclasses.FrozenInstanceError):
        key.run_id = "other"  # type: ignore[misc]


# ── in-memory cache ───────────────────────────────────────────────────────────


def test_inmem_cache_miss_returns_none() -> None:
    cache = BenchmarkCache()
    assert cache.get(make_cache_key(_cfg())) is None


def test_inmem_cache_put_then_get() -> None:
    cache = BenchmarkCache()
    key = make_cache_key(_cfg())
    result = _result()
    cache.put(key, result)
    cached = cache.get(key)
    assert cached is not None
    assert cached.run_id == result.run_id


def test_inmem_cache_contains() -> None:
    cache = BenchmarkCache()
    key = make_cache_key(_cfg())
    assert not cache.contains(key)
    cache.put(key, _result())
    assert cache.contains(key)


def test_inmem_cache_invalidate() -> None:
    cache = BenchmarkCache()
    key = make_cache_key(_cfg())
    cache.put(key, _result())
    cache.invalidate(key)
    assert cache.get(key) is None


def test_inmem_cache_invalidate_missing_is_noop() -> None:
    cache = BenchmarkCache()
    key = make_cache_key(_cfg())
    cache.invalidate(key)  # must not raise


def test_inmem_cache_clear() -> None:
    cache = BenchmarkCache()
    keys = [make_cache_key(_cfg(run_id=f"r{i}")) for i in range(3)]
    for k in keys:
        cache.put(k, _result(run_id=k.run_id))
    cache.clear()
    for k in keys:
        assert cache.get(k) is None


def test_inmem_cache_result_round_trips_mean() -> None:
    cache = BenchmarkCache()
    key = make_cache_key(_cfg())
    result = _result()
    cache.put(key, result)
    cached = cache.get(key)
    assert cached is not None
    assert pytest.approx(cached.metric_results[0].mean) == result.metric_results[0].mean


def test_inmem_cache_separate_keys_do_not_collide() -> None:
    cache = BenchmarkCache()
    ka = make_cache_key(_cfg(run_id="a"))
    kb = make_cache_key(_cfg(run_id="b"))
    cache.put(ka, _result("a"))
    cache.put(kb, _result("b"))
    assert cache.get(ka).run_id == "a"  # type: ignore[union-attr]
    assert cache.get(kb).run_id == "b"  # type: ignore[union-attr]


# ── filesystem cache ──────────────────────────────────────────────────────────


def test_disk_cache_put_creates_file(tmp_path: Path) -> None:
    cache = BenchmarkCache(cache_dir=tmp_path)
    key = make_cache_key(_cfg())
    cache.put(key, _result())
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1


def test_disk_cache_get_after_new_instance(tmp_path: Path) -> None:
    key = make_cache_key(_cfg())
    BenchmarkCache(cache_dir=tmp_path).put(key, _result("persisted"))
    cache2 = BenchmarkCache(cache_dir=tmp_path)
    cached = cache2.get(key)
    assert cached is not None
    assert cached.run_id == "persisted"


def test_disk_cache_invalidate_removes_file(tmp_path: Path) -> None:
    cache = BenchmarkCache(cache_dir=tmp_path)
    key = make_cache_key(_cfg())
    cache.put(key, _result())
    cache.invalidate(key)
    assert not list(tmp_path.glob("*.json"))
    assert cache.get(key) is None


def test_disk_cache_clear_removes_all_files(tmp_path: Path) -> None:
    cache = BenchmarkCache(cache_dir=tmp_path)
    for i in range(3):
        k = make_cache_key(_cfg(run_id=f"r{i}"))
        cache.put(k, _result(f"r{i}"))
    cache.clear()
    assert not list(tmp_path.glob("*.json"))


# ── corruption handling ───────────────────────────────────────────────────────


def test_disk_cache_corrupt_json_raises_cache_error(tmp_path: Path) -> None:
    cache = BenchmarkCache(cache_dir=tmp_path)
    key = make_cache_key(_cfg())
    cache.put(key, _result())
    # Overwrite the file with garbage
    entry_file = next(tmp_path.glob("*.json"))
    entry_file.write_text("not valid json", encoding="utf-8")
    cache2 = BenchmarkCache(cache_dir=tmp_path)
    with pytest.raises(CacheError):
        cache2.get(key)


def test_disk_cache_missing_fields_raises_cache_error(tmp_path: Path) -> None:
    cache = BenchmarkCache(cache_dir=tmp_path)
    key = make_cache_key(_cfg())
    cache.put(key, _result())
    entry_file = next(tmp_path.glob("*.json"))
    entry_file.write_text(json.dumps({"run_id": "x"}), encoding="utf-8")
    cache2 = BenchmarkCache(cache_dir=tmp_path)
    with pytest.raises(CacheError):
        cache2.get(key)


def test_disk_cache_stale_entry_after_fixture_change(tmp_path: Path) -> None:
    """Changing the fixture content invalidates the cache key."""
    fake_fixture = tmp_path / "fixture.json"
    fake_fixture.write_text(
        json.dumps({"cases": [], "format_version": "1.0"}), encoding="utf-8"
    )
    cfg = BenchmarkConfig(
        fixture_path=str(fake_fixture), run_id="stale", k=5,
        metric_names=("precision",),
    )
    cache = BenchmarkCache()
    key_before = make_cache_key(cfg)
    cache.put(key_before, _result("before"))

    # Modify the fixture — hash changes
    fake_fixture.write_text(
        json.dumps({"cases": [{"id": "x"}], "format_version": "1.0"}),
        encoding="utf-8",
    )
    key_after = make_cache_key(cfg)
    assert key_before.digest() != key_after.digest()
    assert cache.get(key_after) is None


# ── retriever identity ────────────────────────────────────────────────────────


def test_retriever_key_has_retriever_name() -> None:
    key = make_retriever_cache_key(_cfg(), "bm25")
    assert key.retriever_name == "bm25"


def test_retriever_key_different_retriever_different_digest() -> None:
    key_bm25 = make_retriever_cache_key(_cfg(), "bm25")
    key_inmem = make_retriever_cache_key(_cfg(), "in_memory")
    assert key_bm25.digest() != key_inmem.digest()


def test_retriever_key_same_retriever_same_digest() -> None:
    k1 = make_retriever_cache_key(_cfg(run_id="r", seed=5), "bm25")
    k2 = make_retriever_cache_key(_cfg(run_id="r", seed=5), "bm25")
    assert k1.digest() == k2.digest()


def test_retriever_key_differs_from_plain_cache_key() -> None:
    plain = make_cache_key(_cfg())
    retriever = make_retriever_cache_key(_cfg(), "bm25")
    assert plain.digest() != retriever.digest()


def test_retriever_key_empty_name_equals_plain_key() -> None:
    plain = make_cache_key(_cfg())
    empty_retriever = make_retriever_cache_key(_cfg(), "")
    assert plain.digest() == empty_retriever.digest()


def test_different_retrievers_cannot_share_cached_result() -> None:
    cache = BenchmarkCache()
    key_bm25 = make_retriever_cache_key(_cfg(), "bm25")
    key_vec = make_retriever_cache_key(_cfg(), "vector")
    cache.put(key_bm25, _result("bm25-run"))
    # A different retriever must not find the bm25 result
    assert cache.get(key_vec) is None


def test_different_retrievers_store_independently() -> None:
    cache = BenchmarkCache()
    key_bm25 = make_retriever_cache_key(_cfg(), "bm25")
    key_vec = make_retriever_cache_key(_cfg(), "vector")
    cache.put(key_bm25, _result("bm25-run"))
    cache.put(key_vec, _result("vec-run"))
    assert cache.get(key_bm25).run_id == "bm25-run"  # type: ignore[union-attr]
    assert cache.get(key_vec).run_id == "vec-run"  # type: ignore[union-attr]


def test_retriever_key_digest_is_deterministic() -> None:
    k1 = make_retriever_cache_key(_cfg(run_id="det", seed=0), "bm25")
    k2 = make_retriever_cache_key(_cfg(run_id="det", seed=0), "bm25")
    assert k1.digest() == k2.digest()


def test_retriever_key_different_seed_different_digest() -> None:
    k1 = make_retriever_cache_key(_cfg(seed=1), "bm25")
    k2 = make_retriever_cache_key(_cfg(seed=2), "bm25")
    assert k1.digest() != k2.digest()


def test_retriever_key_disk_cache_no_cross_retriever_hit(tmp_path: Path) -> None:
    cache = BenchmarkCache(cache_dir=tmp_path)
    key_a = make_retriever_cache_key(_cfg(), "retriever-a")
    cache.put(key_a, _result("a"))
    key_b = make_retriever_cache_key(_cfg(), "retriever-b")
    cache2 = BenchmarkCache(cache_dir=tmp_path)
    assert cache2.get(key_b) is None
