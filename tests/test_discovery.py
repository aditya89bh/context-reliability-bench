from __future__ import annotations

from pathlib import Path

import pytest

from context_reliability_bench.discovery import BenchmarkDiscovery, DiscoveryError
from context_reliability_bench.models.benchmark_metadata import BenchmarkMetadata
from context_reliability_bench.models.manifest import ManifestEntry
from context_reliability_bench.models.versioned_dataset import VersionedDataset

_MANIFEST = Path(__file__).parent.parent / "fixtures" / "manifest.json"


def _discovery() -> BenchmarkDiscovery:
    return BenchmarkDiscovery(_MANIFEST)


def test_from_default_manifest_creates_discovery() -> None:
    d = BenchmarkDiscovery.from_default_manifest()
    assert isinstance(d, BenchmarkDiscovery)


def test_list_datasets_returns_list() -> None:
    datasets = _discovery().list_datasets()
    assert isinstance(datasets, list)


def test_list_datasets_count() -> None:
    assert len(_discovery().list_datasets()) == 5


def test_list_datasets_returns_manifest_entries() -> None:
    for entry in _discovery().list_datasets():
        assert isinstance(entry, ManifestEntry)


def test_categories_returns_all_names() -> None:
    cats = _discovery().categories()
    assert set(cats) == {
        "noise_resistance",
        "contradiction",
        "temporal_relevance",
        "distractor",
        "large_dataset",
    }


def test_get_entry_known_category() -> None:
    entry = _discovery().get_entry("contradiction")
    assert entry.category == "contradiction"


def test_get_entry_unknown_raises() -> None:
    with pytest.raises(DiscoveryError):
        _discovery().get_entry("nonexistent")


def test_metadata_returns_benchmark_metadata() -> None:
    meta = _discovery().metadata("noise_resistance")
    assert isinstance(meta, BenchmarkMetadata)


def test_metadata_fields() -> None:
    meta = _discovery().metadata("noise_resistance")
    assert meta.name == "noise_resistance"
    assert meta.version == "1.0"
    assert meta.category == "noise_resistance"
    assert len(meta.description) > 0


def test_load_dataset_returns_versioned_dataset() -> None:
    ds = _discovery().load_dataset("noise_resistance")
    assert isinstance(ds, VersionedDataset)


def test_load_dataset_category_matches() -> None:
    ds = _discovery().load_dataset("contradiction")
    assert ds.category == "contradiction"


def test_load_dataset_cases_nonempty() -> None:
    for cat in _discovery().categories():
        ds = _discovery().load_dataset(cat)
        assert len(ds) > 0


def test_load_dataset_unknown_raises() -> None:
    with pytest.raises(DiscoveryError):
        _discovery().load_dataset("nonexistent")
