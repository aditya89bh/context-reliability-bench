"""Tests for version consistency validation."""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

from context_reliability_bench import __version__
from context_reliability_bench.version_check import (
    VersionReport,
    VersionSources,
    check_versions,
)

_ROOT = Path(__file__).parent.parent
_PYPROJECT = _ROOT / "pyproject.toml"
_CHANGELOG = _ROOT / "CHANGELOG.md"


# ── pyproject.toml ────────────────────────────────────────────────────────────


def test_pyproject_version_is_semver() -> None:
    text = _PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert m is not None, "version key not found in pyproject.toml"
    ver = m.group(1)
    assert re.fullmatch(r"\d+\.\d+\.\d+", ver), f"Not semver: {ver!r}"


def test_pyproject_version_matches_package() -> None:
    text = _PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert m is not None
    assert m.group(1) == __version__, (
        f"pyproject.toml ({m.group(1)}) != __version__ ({__version__})"
    )


def test_package_version_is_string() -> None:
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_package_version_is_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__), (
        f"__version__ is not semver: {__version__!r}"
    )


# ── CHANGELOG.md ──────────────────────────────────────────────────────────────


def test_changelog_exists() -> None:
    assert _CHANGELOG.exists()


def test_changelog_has_unreleased_section() -> None:
    text = _CHANGELOG.read_text(encoding="utf-8")
    assert "## [Unreleased]" in text, "CHANGELOG must have an [Unreleased] section"


def test_changelog_unreleased_link_points_to_real_repo() -> None:
    text = _CHANGELOG.read_text(encoding="utf-8")
    m = re.search(r"\[Unreleased\]:\s*(https?://\S+)", text)
    assert m is not None, "[Unreleased] link not found in CHANGELOG"
    url = m.group(1)
    assert "example.com" not in url, f"Placeholder URL still present: {url}"
    assert "aditya89bh" in url or "github.com" in url, (
        f"Expected real GitHub URL, got: {url}"
    )


# ── check_versions() ──────────────────────────────────────────────────────────


def test_check_versions_returns_report() -> None:
    report = check_versions()
    assert isinstance(report, VersionReport)


def test_check_versions_sources_type() -> None:
    report = check_versions()
    assert isinstance(report.sources, VersionSources)


def test_check_versions_consistent() -> None:
    report = check_versions()
    assert report.consistent, "\n".join(report.messages)


def test_check_versions_pyproject_matches_package() -> None:
    report = check_versions()
    assert report.sources.pyproject == report.sources.package


def test_check_versions_has_messages() -> None:
    report = check_versions()
    assert len(report.messages) > 0


def test_check_versions_sources_has_changelog_version_field() -> None:
    report = check_versions()
    # changelog_version is either a version string or None — never missing
    assert hasattr(report.sources, "changelog_version")
    cv = report.sources.changelog_version
    assert cv is None or isinstance(cv, str)


# ── lifecycle-aware consistency checks ────────────────────────────────────────
# These tests pass in BOTH pre-release and post-release states.


def test_pre_release_state_requires_unreleased_section() -> None:
    """When no git tag exists, CHANGELOG must have [Unreleased]."""
    report = check_versions()
    if report.sources.git_tag is None:
        assert report.sources.changelog_unreleased, (
            "Pre-release: no git tag exists but [Unreleased] section is missing"
        )


def test_post_release_state_requires_version_section() -> None:
    """When a git tag exists, CHANGELOG must have a matching version section."""
    report = check_versions()
    if report.sources.git_tag is not None:
        assert report.sources.changelog_version == report.sources.pyproject, (
            f"Post-release: tag {report.sources.git_tag} exists but "
            f"[{report.sources.pyproject}] section is missing in CHANGELOG"
        )


def test_exactly_one_lifecycle_state_is_active() -> None:
    """The repo is in pre-release OR post-release state, not ambiguous."""
    report = check_versions()
    has_tag = report.sources.git_tag is not None
    has_version_section = report.sources.changelog_version is not None
    # In pre-release: no tag, no version section is expected
    # In post-release: tag and version section both present
    if has_tag:
        assert has_version_section, (
            "Post-release detected (tag exists) but changelog_version is None"
        )
    else:
        assert report.sources.changelog_unreleased, (
            "Pre-release detected (no tag) but [Unreleased] section is missing"
        )


# ── VersionSources is frozen ──────────────────────────────────────────────────


def test_version_sources_frozen() -> None:
    sources = check_versions().sources
    with pytest.raises(dataclasses.FrozenInstanceError):
        sources.pyproject = "9.9.9"  # type: ignore[misc]


def test_version_report_frozen() -> None:
    report = check_versions()
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.consistent = False  # type: ignore[misc]
