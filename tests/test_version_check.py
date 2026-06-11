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


def test_changelog_no_invented_release_tags() -> None:
    text = _CHANGELOG.read_text(encoding="utf-8")
    # Versioned release sections look like "## [0.x.y]"
    released = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    assert released == [], (
        f"CHANGELOG contains versioned release sections that were never published: "
        f"{released}"
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


def test_check_versions_no_tag_before_release() -> None:
    report = check_versions()
    # We are pre-release: no git tag should exist yet
    assert report.sources.git_tag is None, (
        f"Unexpected git tag {report.sources.git_tag} — package is unreleased"
    )


def test_check_versions_unreleased_section_present() -> None:
    report = check_versions()
    assert report.sources.changelog_unreleased, (
        "CHANGELOG must have [Unreleased] section while no release tag exists"
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
