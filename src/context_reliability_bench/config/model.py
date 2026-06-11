from __future__ import annotations

from dataclasses import dataclass, field


class ConfigError(Exception):
    pass


def _empty_frozenset() -> frozenset[str]:
    return frozenset()


_DEFAULT_METRICS: tuple[str, ...] = (
    "precision",
    "recall",
    "ndcg",
    "mrr",
    "top_k_accuracy",
)


@dataclass(frozen=True)
class BenchmarkConfig:
    fixture_path: str
    run_id: str = "default"
    k: int = 5
    metric_names: tuple[str, ...] = _DEFAULT_METRICS
    output_json: str | None = None
    output_csv: str | None = None
    tags: frozenset[str] = field(default_factory=_empty_frozenset)
    seed: int | None = None
