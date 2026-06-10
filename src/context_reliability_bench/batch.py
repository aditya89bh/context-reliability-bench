from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from context_reliability_bench.config.model import BenchmarkConfig
from context_reliability_bench.loader import FixtureError, load_fixture
from context_reliability_bench.metrics.mrr import ReciprocalRank
from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.metrics.top_k_accuracy import TopKAccuracy
from context_reliability_bench.models.run_result import RunResult
from context_reliability_bench.runner import run_benchmark
from context_reliability_bench.scoring import aggregate_score


class BatchError(Exception):
    pass


@dataclass(frozen=True)
class BatchResult:
    results: tuple[RunResult, ...]

    def get_by_run_id(self, run_id: str) -> RunResult | None:
        for r in self.results:
            if r.run_id == run_id:
                return r
        return None

    def all_passed(self, min_aggregate_score: float) -> bool:
        return all(
            aggregate_score(r) >= min_aggregate_score for r in self.results
        )


def run_batch(configs: list[BenchmarkConfig]) -> BatchResult:
    if not configs:
        raise ValueError("configs must not be empty")

    results: list[RunResult] = []
    for config in configs:
        try:
            cases = load_fixture(Path(config.fixture_path))
        except FixtureError as exc:
            raise BatchError(
                f"Failed to load fixture '{config.fixture_path}': {exc}"
            ) from exc

        metrics = _build_metrics(config)
        result = run_benchmark(cases, metrics, run_id=config.run_id)
        results.append(result)

    return BatchResult(results=tuple(results))


def _build_metrics(config: BenchmarkConfig) -> list[Metric]:
    metrics: list[Metric] = []
    for name in config.metric_names:
        if name == "precision":
            metrics.append(PrecisionAtK(k=config.k))
        elif name == "recall":
            metrics.append(RecallAtK(k=config.k))
        elif name == "ndcg":
            metrics.append(NdcgAtK(k=config.k))
        elif name == "mrr":
            metrics.append(ReciprocalRank())
        elif name == "top_k_accuracy":
            metrics.append(TopKAccuracy(k=config.k))
    if not metrics:
        metrics.append(PrecisionAtK(k=config.k))
    return metrics
