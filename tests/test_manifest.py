from __future__ import annotations

from pathlib import Path

import pytest

from context_reliability_bench.models.manifest import (
    DatasetManifest,
    ManifestEntry,
    ManifestError,
    load_manifest,
)

_MANIFEST_PATH = Path(__file__).parent.parent / "fixtures" / "manifest.json"


def test_load_manifest_returns_dataset_manifest() -> None:
    manifest = load_manifest(_MANIFEST_PATH)
    assert isinstance(manifest, DatasetManifest)


def test_manifest_version() -> None:
    manifest = load_manifest(_MANIFEST_PATH)
    assert manifest.manifest_version == "1.0"


def test_manifest_has_four_datasets() -> None:
    manifest = load_manifest(_MANIFEST_PATH)
    assert len(manifest.datasets) == 4


def test_manifest_categories_list() -> None:
    manifest = load_manifest(_MANIFEST_PATH)
    cats = manifest.categories()
    assert set(cats) == {
        "noise_resistance",
        "contradiction",
        "temporal_relevance",
        "distractor",
    }


def test_manifest_get_known_category() -> None:
    manifest = load_manifest(_MANIFEST_PATH)
    entry = manifest.get("noise_resistance")
    assert entry is not None
    assert isinstance(entry, ManifestEntry)


def test_manifest_get_unknown_returns_none() -> None:
    manifest = load_manifest(_MANIFEST_PATH)
    assert manifest.get("nonexistent") is None


def test_manifest_entry_fields() -> None:
    manifest = load_manifest(_MANIFEST_PATH)
    entry = manifest.get("noise_resistance")
    assert entry is not None
    assert entry.category == "noise_resistance"
    assert entry.format_version == "1.0"
    assert entry.path == "v1/noise_resistance.json"
    assert len(entry.description) > 0
    assert entry.case_count == 3


def test_manifest_entry_case_count_positive() -> None:
    manifest = load_manifest(_MANIFEST_PATH)
    for entry in manifest.datasets:
        assert entry.case_count > 0


def test_load_manifest_missing_file_raises() -> None:
    with pytest.raises(ManifestError):
        load_manifest(Path("/no/such/manifest.json"))


def test_load_manifest_invalid_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "manifest.json"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(ManifestError):
        load_manifest(bad)


def test_load_manifest_missing_datasets_field(tmp_path: Path) -> None:
    bad = tmp_path / "manifest.json"
    bad.write_text('{"manifest_version": "1.0"}', encoding="utf-8")
    manifest = load_manifest(bad)
    assert len(manifest.datasets) == 0
