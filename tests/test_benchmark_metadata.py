from __future__ import annotations

from context_reliability_bench.models.benchmark_metadata import BenchmarkMetadata


def test_create_with_required_fields() -> None:
    m = BenchmarkMetadata(
        name="noise_resistance",
        version="1.0",
        description="Tests noise in retrieval.",
        category="noise_resistance",
    )
    assert m.name == "noise_resistance"
    assert m.version == "1.0"
    assert m.description == "Tests noise in retrieval."
    assert m.category == "noise_resistance"


def test_tags_default_to_empty_frozenset() -> None:
    m = BenchmarkMetadata(
        name="x", version="1", description="d", category="c"
    )
    assert m.tags == frozenset()


def test_tags_type_is_frozenset() -> None:
    m = BenchmarkMetadata(
        name="x", version="1", description="d", category="c"
    )
    assert isinstance(m.tags, frozenset)


def test_create_with_tags() -> None:
    m = BenchmarkMetadata(
        name="x",
        version="1",
        description="d",
        category="c",
        tags=frozenset({"retrieval", "rag"}),
    )
    assert "retrieval" in m.tags
    assert "rag" in m.tags


def test_is_frozen() -> None:
    import dataclasses

    m = BenchmarkMetadata(
        name="x", version="1", description="d", category="c"
    )
    try:
        m.name = "y"  # type: ignore[misc]
        raise AssertionError("Expected FrozenInstanceError")
    except dataclasses.FrozenInstanceError:
        pass


def test_equality() -> None:
    m1 = BenchmarkMetadata(name="x", version="1", description="d", category="c")
    m2 = BenchmarkMetadata(name="x", version="1", description="d", category="c")
    assert m1 == m2


def test_inequality_different_version() -> None:
    m1 = BenchmarkMetadata(name="x", version="1", description="d", category="c")
    m2 = BenchmarkMetadata(name="x", version="2", description="d", category="c")
    assert m1 != m2
