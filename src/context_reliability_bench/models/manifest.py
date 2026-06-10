from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ManifestError(Exception):
    pass


@dataclass(frozen=True)
class ManifestEntry:
    category: str
    format_version: str
    path: str
    description: str
    case_count: int


@dataclass(frozen=True)
class DatasetManifest:
    manifest_version: str
    datasets: tuple[ManifestEntry, ...]

    def get(self, category: str) -> ManifestEntry | None:
        for entry in self.datasets:
            if entry.category == category:
                return entry
        return None

    def categories(self) -> list[str]:
        return [entry.category for entry in self.datasets]


def load_manifest(path: Path) -> DatasetManifest:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(f"Cannot read manifest: {path}") from exc
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Invalid JSON in manifest: {path}") from exc
    return _parse_manifest(payload)


def _parse_manifest(payload: Any) -> DatasetManifest:
    if not isinstance(payload, dict):
        raise ManifestError("Manifest must be a JSON object")
    mv = payload.get("manifest_version", "unknown")
    manifest_version = mv if isinstance(mv, str) else "unknown"
    datasets_raw = payload.get("datasets", [])
    if not isinstance(datasets_raw, list):
        raise ManifestError("Manifest 'datasets' must be a JSON array")
    datasets = tuple(
        _parse_entry(e, i) for i, e in enumerate(datasets_raw)
    )
    return DatasetManifest(
        manifest_version=manifest_version,
        datasets=datasets,
    )


def _parse_entry(raw: Any, index: int) -> ManifestEntry:
    loc = f"datasets[{index}]"
    if not isinstance(raw, dict):
        raise ManifestError(f"{loc} must be a JSON object")
    category = raw.get("category")
    format_version = raw.get("format_version")
    path_str = raw.get("path")
    description = raw.get("description", "")
    case_count = raw.get("case_count", 0)
    if not isinstance(category, str):
        raise ManifestError(f"{loc}.category must be a string")
    if not isinstance(format_version, str):
        raise ManifestError(f"{loc}.format_version must be a string")
    if not isinstance(path_str, str):
        raise ManifestError(f"{loc}.path must be a string")
    if not isinstance(description, str):
        raise ManifestError(f"{loc}.description must be a string")
    if not isinstance(case_count, int) or isinstance(case_count, bool):
        raise ManifestError(f"{loc}.case_count must be an integer")
    return ManifestEntry(
        category=category,
        format_version=format_version,
        path=path_str,
        description=description,
        case_count=case_count,
    )
