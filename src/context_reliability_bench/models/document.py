from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    id: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)
