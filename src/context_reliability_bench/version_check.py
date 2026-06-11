"""Utilities for verifying version consistency across project artefacts."""

from __future__ import annotations

import importlib.metadata
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent

# True when running from a source checkout; False when installed as a wheel.
_IS_SOURCE = (_ROOT / "pyproject.toml").exists()


@dataclass(frozen=True)
class VersionSources:
    pyproject: str
    package: str
    changelog_unreleased: bool
    git_tag: str | None
    changelog_version: str | None  # e.g. "0.1.0" if [0.1.0] section present


@dataclass(frozen=True)
class VersionReport:
    sources: VersionSources
    consistent: bool
    messages: tuple[str, ...]


def _read_pyproject_version() -> str:
    if _IS_SOURCE:
        text = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if not m:
            raise ValueError("version not found in pyproject.toml")
        return m.group(1)
    return importlib.metadata.version("context-reliability-bench")


def _read_package_version() -> str:
    from context_reliability_bench import __version__
    return __version__


def _read_changelog_unreleased() -> bool:
    changelog = _ROOT / "CHANGELOG.md"
    if not changelog.exists():
        return False
    text = changelog.read_text(encoding="utf-8")
    return bool(re.search(r"^## \[Unreleased\]", text, re.MULTILINE))


def _read_changelog_version(version: str) -> str | None:
    """Return ``version`` if a ``## [version]`` section exists in CHANGELOG."""
    changelog = _ROOT / "CHANGELOG.md"
    if not changelog.exists():
        return None
    text = changelog.read_text(encoding="utf-8")
    escaped = re.escape(version)
    m = re.search(rf"^## \[{escaped}\]", text, re.MULTILINE)
    return version if m else None


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
        if result.returncode != 0:
            msg = result.stderr.strip() or "git status returned non-zero"
            return (False, [msg])
        files = dirty_files(result.stdout)
        return (not files, files)
    except (subprocess.SubprocessError, FileNotFoundError):
        return (False, ["git not available"])


def check_versions() -> VersionReport:
    """Return a VersionReport describing cross-artefact version consistency.

    Two valid lifecycle states (source checkouts only):
    - Pre-release: no git tag, CHANGELOG has [Unreleased] section.
    - Post-release: git tag v{version} exists, CHANGELOG has [{version}] section.
      An [Unreleased] section may also be present for future work.

    When running from an installed wheel (no pyproject.toml on disk) only the
    pyproject == package version check is performed.
    """
    pyproject = _read_pyproject_version()
    package = _read_package_version()
    changelog_unreleased = _read_changelog_unreleased()
    changelog_version = _read_changelog_version(pyproject)
    git_tag = _read_git_tag(pyproject)

    messages: list[str] = []
    consistent = True

    if pyproject != package:
        consistent = False
        messages.append(
            f"pyproject.toml version ({pyproject}) != "
            f"package __version__ ({package})"
        )

    if _IS_SOURCE:
        if git_tag is None:
            # Pre-release: CHANGELOG must have [Unreleased] section
            if not changelog_unreleased:
                consistent = False
                messages.append(
                    f"Pre-release: no git tag v{pyproject} and no [Unreleased] "
                    f"section in CHANGELOG"
                )
        else:
            # Post-release: CHANGELOG must have [{version}] section.
            # An [Unreleased] section for future work is allowed.
            if changelog_version is None:
                consistent = False
                messages.append(
                    f"Git tag {git_tag} exists but CHANGELOG has no "
                    f"[{pyproject}] section"
                )

    if consistent and not messages:
        messages.append(f"All version sources agree on {pyproject}")

    sources = VersionSources(
        pyproject=pyproject,
        package=package,
        changelog_unreleased=changelog_unreleased,
        git_tag=git_tag,
        changelog_version=changelog_version,
    )
    return VersionReport(
        sources=sources,
        consistent=consistent,
        messages=tuple(messages),
    )
