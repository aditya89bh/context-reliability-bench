from __future__ import annotations

from pathlib import Path

from context_reliability_bench.models.benchmark_metadata import BenchmarkMetadata
from context_reliability_bench.models.manifest import (
    DatasetManifest,
    ManifestEntry,
    load_manifest,
)
from context_reliability_bench.models.versioned_dataset import VersionedDataset

_DEFAULT_MANIFEST_PATH = (
    Path(__file__).parent.parent.parent / "fixtures" / "manifest.json"
)


class DiscoveryError(Exception):
    pass


class BenchmarkDiscovery:
    def __init__(self, manifest_path: Path) -> None:
        self._manifest: DatasetManifest = load_manifest(manifest_path)
        self._manifest_dir: Path = manifest_path.parent

    @classmethod
    def from_default_manifest(cls) -> BenchmarkDiscovery:
        return cls(_DEFAULT_MANIFEST_PATH)

    def list_datasets(self) -> list[ManifestEntry]:
        return list(self._manifest.datasets)

    def categories(self) -> list[str]:
        return self._manifest.categories()

    def get_entry(self, category: str) -> ManifestEntry:
        entry = self._manifest.get(category)
        if entry is None:
            raise DiscoveryError(
                f"Category '{category}' not found in manifest."
            )
        return entry

    def metadata(self, category: str) -> BenchmarkMetadata:
        entry = self.get_entry(category)
        return BenchmarkMetadata(
            name=entry.category,
            version=entry.format_version,
            description=entry.description,
            category=entry.category,
        )

    def load_dataset(self, category: str) -> VersionedDataset:
        from context_reliability_bench.loader import (
            FixtureError,
            load_versioned_fixture,
        )

        entry = self.get_entry(category)
        fixture_path = self._manifest_dir / entry.path
        try:
            return load_versioned_fixture(fixture_path)
        except FixtureError as exc:
            raise DiscoveryError(
                f"Cannot load dataset for '{category}': {exc}"
            ) from exc
