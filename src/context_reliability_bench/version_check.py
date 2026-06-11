"""Utilities for verifying version consistency across project artefacts."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent


@dataclass(frozen=True)
class VersionSources:
    pyproject: str
    package: str
    changelog_unreleased: bool  # True = Unreleased section present (no released tag)
    git_tag: str | None  # e.g. "v0.1.0", or None if no tags match


@dataclass(frozen=True)
class VersionReport:
    sources: VersionSources
    consistent: bool
    messages: tuple[str, ...]


def _read_pyproject_version() -> str:
    text = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        raise ValueError("version not found in pyproject.toml")
    return m.group(1)


def _read_package_version() -> str:
    from context_reliability_bench import __version__
    return __version__


def _read_changelog_unreleased() -> bool:
    text = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    return bool(re.search(r"^## \[Unreleased\]", text, re.MULTILINE))


def _read_git_tag(version: str) -> str | None:
    tag = f"v{version}"
    try:
        result = subprocess.run(
            ["git", "tag", "--list", tag],
            capture_output=True,
            text=True,
            cwd=_ROOT,
            timeout=10,
        )
        return tag if result.stdout.strip() == tag else None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def dirty_files(porcelain_output: str) -> list[str]:
    """Return non-empty lines from ``git status --porcelain`` output.

    Every line represents a file that is modified, staged, or untracked.
    `git status --porcelain` already excludes gitignored files, so no extra
    filtering is needed.
    """
    return [line for line in porcelain_output.splitlines() if line]


def repo_is_clean(root: Path = _ROOT) -> tuple[bool, list[str]]:
    """Return (True, []) when the working tree is clean, else (False, dirty_lines)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=root,
            timeout=10,
        )
        files = dirty_files(result.stdout)
        return (not files, files)
    except (subprocess.SubprocessError, FileNotFoundError):
        return (False, ["git not available"])


def check_versions() -> VersionReport:
    """Return a VersionReport describing cross-artefact version consistency."""
    pyproject = _read_pyproject_version()
    package = _read_package_version()
    changelog_unreleased = _read_changelog_unreleased()
    git_tag = _read_git_tag(pyproject)

    messages: list[str] = []
    consistent = True

    if pyproject != package:
        consistent = False
        messages.append(
            f"pyproject.toml version ({pyproject}) != "
            f"package __version__ ({package})"
        )

    if not changelog_unreleased and git_tag is None:
        consistent = False
        messages.append(
            f"No [Unreleased] section in CHANGELOG and no git tag v{pyproject}"
        )

    if git_tag is not None and changelog_unreleased:
        messages.append(
            f"Git tag {git_tag} exists but CHANGELOG still has [Unreleased] section"
        )

    if consistent and not messages:
        messages.append(f"All version sources agree on {pyproject}")

    sources = VersionSources(
        pyproject=pyproject,
        package=package,
        changelog_unreleased=changelog_unreleased,
        git_tag=git_tag,
    )
    return VersionReport(
        sources=sources,
        consistent=consistent,
        messages=tuple(messages),
    )
