from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TimingRecord:
    """Wall-clock timing for one phase of a benchmark run."""

    label: str
    elapsed_seconds: float

    @property
    def elapsed_ms(self) -> float:
        return self.elapsed_seconds * 1000.0


@dataclass(frozen=True)
class BenchmarkTiming:
    """Aggregated timing records for a benchmark run."""

    records: tuple[TimingRecord, ...]

    def get(self, label: str) -> TimingRecord | None:
        for r in self.records:
            if r.label == label:
                return r
        return None

    @property
    def total_seconds(self) -> float:
        return sum(r.elapsed_seconds for r in self.records)

    def as_dict(self) -> dict[str, float]:
        return {r.label: r.elapsed_seconds for r in self.records}


class _Timer:
    """Context manager that records elapsed wall-clock time."""

    def __init__(self) -> None:
        self._start: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self) -> _Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_: Any) -> None:
        self.elapsed = time.perf_counter() - self._start


def time_benchmark(
    fn: Any,
    *args: Any,
    label: str = "benchmark",
    **kwargs: Any,
) -> tuple[Any, TimingRecord]:
    """Call *fn* with *args*/*kwargs* and return (result, TimingRecord)."""
    timer = _Timer()
    with timer:
        result = fn(*args, **kwargs)
    return result, TimingRecord(label=label, elapsed_seconds=timer.elapsed)
