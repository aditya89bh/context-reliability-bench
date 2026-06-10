from __future__ import annotations

from enum import Enum

from context_reliability_bench.config.model import BenchmarkConfig


class ExecutionProfile(Enum):
    QUICK = "quick"
    STANDARD = "standard"
    THOROUGH = "thorough"


_PROFILE_K: dict[ExecutionProfile, int] = {
    ExecutionProfile.QUICK: 3,
    ExecutionProfile.STANDARD: 5,
    ExecutionProfile.THOROUGH: 10,
}

_PROFILE_METRICS: dict[ExecutionProfile, tuple[str, ...]] = {
    ExecutionProfile.QUICK: ("precision", "recall"),
    ExecutionProfile.STANDARD: (
        "precision",
        "recall",
        "ndcg",
        "mrr",
        "top_k_accuracy",
    ),
    ExecutionProfile.THOROUGH: (
        "precision",
        "recall",
        "ndcg",
        "mrr",
        "top_k_accuracy",
    ),
}


def config_from_profile(
    fixture_path: str,
    profile: ExecutionProfile,
    run_id: str = "default",
    tags: frozenset[str] | None = None,
) -> BenchmarkConfig:
    return BenchmarkConfig(
        fixture_path=fixture_path,
        run_id=run_id,
        k=_PROFILE_K[profile],
        metric_names=_PROFILE_METRICS[profile],
        tags=tags if tags is not None else frozenset(),
    )
