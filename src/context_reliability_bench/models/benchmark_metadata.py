from __future__ import annotations

from dataclasses import dataclass, field


def _default_tags() -> frozenset[str]:
    return frozenset()


@dataclass(frozen=True)
class BenchmarkMetadata:
    name: str
    version: str
    description: str
    category: str
    tags: frozenset[str] = field(default_factory=_default_tags)
