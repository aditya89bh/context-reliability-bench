from __future__ import annotations

from pathlib import Path

import pytest

from context_reliability_bench.loader import FixtureError, load_versioned_fixture
from context_reliability_bench.models.benchmark_case import BenchmarkCase
from context_reliability_bench.models.versioned_dataset import VersionedDataset

_ROOT = Path(__file__).parent.parent
_NOISE_FIXTURE = _ROOT / "fixtures" / "v1" / "noise_resistance.json"
_SAMPLE_FIXTURE = _ROOT / "fixtures" / "sample.json"


def test_returns_versioned_dataset() -> None:
    ds = load_versioned_fixture(_NOISE_FIXTURE)
    assert isinstance(ds, VersionedDataset)


def test_format_version_from_fixture() -> None:
    ds = load_versioned_fixture(_NOISE_FIXTURE)
    assert ds.format_version == "1.0"


def test_category_from_fixture() -> None:
    ds = load_versioned_fixture(_NOISE_FIXTURE)
    assert ds.category == "noise_resistance"


def test_cases_count() -> None:
    ds = load_versioned_fixture(_NOISE_FIXTURE)
    assert len(ds) == 3


def test_len_matches_cases_tuple() -> None:
    ds = load_versioned_fixture(_NOISE_FIXTURE)
    assert len(ds) == len(ds.cases)


def test_cases_are_benchmark_case_instances() -> None:
    ds = load_versioned_fixture(_NOISE_FIXTURE)
    for case in ds.cases:
        assert isinstance(case, BenchmarkCase)


def test_missing_format_version_defaults_to_unknown() -> None:
    ds = load_versioned_fixture(_SAMPLE_FIXTURE)
    assert ds.format_version == "unknown"


def test_missing_category_defaults_to_unknown() -> None:
    ds = load_versioned_fixture(_SAMPLE_FIXTURE)
    assert ds.category == "unknown"


def test_missing_file_raises_fixture_error() -> None:
    with pytest.raises(FixtureError):
        load_versioned_fixture(Path("/no/such/file.json"))


def test_all_v1_fixtures_parse_with_version() -> None:
    for name in (
        "noise_resistance",
        "contradiction",
        "temporal_relevance",
        "distractor",
    ):
        ds = load_versioned_fixture(
            _ROOT / "fixtures" / "v1" / f"{name}.json"
        )
        assert ds.format_version == "1.0"
        assert ds.category == name
