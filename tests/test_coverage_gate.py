"""Assert the minimum coverage threshold is declared in pyproject.toml."""

from __future__ import annotations

import re
from pathlib import Path

_PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"
_MIN_COVERAGE = 80


def test_coverage_threshold_declared() -> None:
    text = _PYPROJECT.read_text()
    match = re.search(r"fail_under\s*=\s*(\d+)", text)
    assert match is not None, (
        "fail_under not found in pyproject.toml [tool.coverage.report]"
    )
    assert int(match.group(1)) >= _MIN_COVERAGE, (
        f"fail_under={match.group(1)} is below minimum {_MIN_COVERAGE}"
    )


def test_coverage_section_exists() -> None:
    text = _PYPROJECT.read_text()
    assert "[tool.coverage.report]" in text
    assert "[tool.coverage.run]" in text


def test_coverage_source_is_library() -> None:
    text = _PYPROJECT.read_text()
    assert 'source = ["context_reliability_bench"]' in text
