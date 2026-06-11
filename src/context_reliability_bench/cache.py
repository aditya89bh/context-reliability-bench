from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from context_reliability_bench.config.model import BenchmarkConfig
from context_reliability_bench.models.metric_result import MetricResult
from context_reliability_bench.models.run_result import RunResult


class CacheError(Exception):
    pass


@dataclass(frozen=True)
class CacheKey:
    """Unique identifier for a benchmark result entry.

    *retriever_name* identifies which retriever produced the results.  It is
    the empty string for config-based (pre-computed context) benchmarks.
    Different retrievers must never share a cache entry even when all other
    key components are identical.
    """

    fixture_hash: str
    metric_names: tuple[str, ...]
    k: int
    seed: int | None
    run_id: str
    retriever_name: str = ""

    def digest(self) -> str:
        """SHA-256 hex digest of all key components including retriever identity."""
        raw = json.dumps(
            {
                "fixture_hash": self.fixture_hash,
                "metric_names": list(self.metric_names),
                "k": self.k,
                "seed": self.seed,
                "run_id": self.run_id,
                "retriever_name": self.retriever_name,
            },
            sort_keys=True,
        ).encode()
        return hashlib.sha256(raw).hexdigest()


def _fixture_hash(fixture_path: str) -> str:
    """SHA-256 of the fixture file contents."""
    try:
        data = Path(fixture_path).read_bytes()
    except OSError as exc:
        raise CacheError(f"Cannot hash fixture '{fixture_path}': {exc}") from exc
    return hashlib.sha256(data).hexdigest()


def make_cache_key(config: BenchmarkConfig) -> CacheKey:
    """Build a cache key for a config-based (pre-computed context) benchmark."""
    return CacheKey(
        fixture_hash=_fixture_hash(config.fixture_path),
        metric_names=config.metric_names,
        k=config.k,
        seed=config.seed,
        run_id=config.run_id,
        retriever_name="",
    )


def make_retriever_cache_key(
    config: BenchmarkConfig,
    retriever_name: str,
) -> CacheKey:
    """Build a cache key that includes the retriever's identity.

    Results from different retrievers must never collide even when dataset,
    metrics, k, seed, and run_id are identical.
    """
    return CacheKey(
        fixture_hash=_fixture_hash(config.fixture_path),
        metric_names=config.metric_names,
        k=config.k,
        seed=config.seed,
        run_id=config.run_id,
        retriever_name=retriever_name,
    )


# ── serialisation helpers ─────────────────────────────────────────────────────


def _result_to_dict(result: RunResult) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "seed": result.seed,
        "metric_results": [
            {
                "metric_name": mr.metric_name,
                "mean": mr.mean,
                "case_scores": list(mr.case_scores),
            }
            for mr in result.metric_results
        ],
    }


def _result_from_dict(data: dict[str, Any]) -> RunResult:
    metric_results = tuple(
        MetricResult(
            metric_name=mr["metric_name"],
            mean=mr["mean"],
            case_scores=tuple(tuple(cs) for cs in mr["case_scores"]),
        )
        for mr in data["metric_results"]
    )
    return RunResult(
        run_id=data["run_id"],
        seed=data.get("seed"),
        metric_results=metric_results,
    )


# ── cache implementation ──────────────────────────────────────────────────────


class BenchmarkCache:
    """Stores and retrieves benchmark results keyed by dataset + configuration.

    When *cache_dir* is None, results are kept only in memory for the lifetime
    of this instance.  When a directory path is provided, each entry is
    persisted as a JSON file named by the key digest.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._mem: dict[str, RunResult] = {}
        self._dir = cache_dir
        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)

    # ── public API ────────────────────────────────────────────────────────────

    def get(self, key: CacheKey) -> RunResult | None:
        digest = key.digest()
        if digest in self._mem:
            return self._mem[digest]
        if self._dir is not None:
            return self._load_from_disk(digest)
        return None

    def put(self, key: CacheKey, result: RunResult) -> None:
        digest = key.digest()
        self._mem[digest] = result
        if self._dir is not None:
            self._save_to_disk(digest, result)

    def invalidate(self, key: CacheKey) -> None:
        digest = key.digest()
        self._mem.pop(digest, None)
        if self._dir is not None:
            path = self._entry_path(digest)
            if path.exists():
                path.unlink()

    def clear(self) -> None:
        self._mem.clear()
        if self._dir is not None:
            for path in self._dir.glob("*.json"):
                path.unlink()

    def contains(self, key: CacheKey) -> bool:
        return self.get(key) is not None

    # ── disk I/O ──────────────────────────────────────────────────────────────

    def _entry_path(self, digest: str) -> Path:
        assert self._dir is not None
        return self._dir / f"{digest}.json"

    def _save_to_disk(self, digest: str, result: RunResult) -> None:
        path = self._entry_path(digest)
        payload = json.dumps(_result_to_dict(result), indent=2)
        path.write_text(payload, encoding="utf-8")

    def _load_from_disk(self, digest: str) -> RunResult | None:
        path = self._entry_path(digest)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            result = _result_from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise CacheError(
                f"Corrupt cache entry at '{path}': {exc}"
            ) from exc
        self._mem[digest] = result
        return result
