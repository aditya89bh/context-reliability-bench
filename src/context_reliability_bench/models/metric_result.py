from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricResult:
    metric_name: str
    case_scores: tuple[tuple[str, float], ...]
    mean: float
