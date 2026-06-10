from __future__ import annotations

from dataclasses import dataclass

from context_reliability_bench.history import BenchmarkHistory

_TREND_THRESHOLD: float = 0.01


@dataclass(frozen=True)
class MetricTrend:
    metric_name: str
    values: tuple[float, ...]
    timestamps: tuple[str, ...]
    direction: str
    slope: float


@dataclass(frozen=True)
class TrendAnalysis:
    metric_trends: tuple[MetricTrend, ...]

    def get_trend(self, metric_name: str) -> MetricTrend | None:
        for t in self.metric_trends:
            if t.metric_name == metric_name:
                return t
        return None


def analyze_trends(
    history: BenchmarkHistory,
    metric_names: list[str] | None = None,
) -> TrendAnalysis:
    if len(history.records) < 2:
        return TrendAnalysis(metric_trends=())

    sorted_recs = sorted(history.records, key=lambda r: r.timestamp)

    if metric_names is None:
        metric_names = sorted(
            {
                mr.metric_name
                for record in sorted_recs
                for mr in record.run_result.metric_results
            }
        )

    trends: list[MetricTrend] = []
    for name in metric_names:
        values: list[float] = []
        timestamps: list[str] = []
        for record in sorted_recs:
            for mr in record.run_result.metric_results:
                if mr.metric_name == name:
                    values.append(mr.mean)
                    timestamps.append(record.timestamp)
                    break

        if len(values) < 2:
            continue

        slope = _linear_slope(values)
        direction = _direction(slope)
        trends.append(
            MetricTrend(
                metric_name=name,
                values=tuple(values),
                timestamps=tuple(timestamps),
                direction=direction,
                slope=slope,
            )
        )

    return TrendAnalysis(metric_trends=tuple(trends))


def _linear_slope(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    sum_x = sum(xs)
    sum_y = sum(values)
    sum_xy = sum(x * y for x, y in zip(xs, values, strict=True))
    sum_x2 = sum(x * x for x in xs)
    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        return 0.0
    return (n * sum_xy - sum_x * sum_y) / denom


def _direction(slope: float) -> str:
    if slope > _TREND_THRESHOLD:
        return "improving"
    if slope < -_TREND_THRESHOLD:
        return "degrading"
    return "stable"
