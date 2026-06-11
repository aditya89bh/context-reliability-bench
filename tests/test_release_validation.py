"""Tests for repository cleanliness helpers in version_check."""

from __future__ import annotations

from context_reliability_bench.version_check import dirty_files


def test_dirty_files_empty_output_returns_empty_list() -> None:
    assert dirty_files("") == []


def test_dirty_files_modified_unstaged() -> None:
    output = " M src/context_reliability_bench/version_check.py"
    result = dirty_files(output)
    assert result == [" M src/context_reliability_bench/version_check.py"]


def test_dirty_files_staged() -> None:
    output = "M  src/context_reliability_bench/version_check.py"
    result = dirty_files(output)
    assert result == ["M  src/context_reliability_bench/version_check.py"]


def test_dirty_files_untracked() -> None:
    output = "?? newfile.py"
    result = dirty_files(output)
    assert result == ["?? newfile.py"]


def test_dirty_files_all_three_kinds() -> None:
    output = "\n".join([
        " M modified.py",
        "M  staged.py",
        "?? untracked.py",
    ])
    result = dirty_files(output)
    assert len(result) == 3
    assert " M modified.py" in result
    assert "M  staged.py" in result
    assert "?? untracked.py" in result


def test_dirty_files_ignores_blank_lines() -> None:
    output = " M file.py\n\n?? other.py\n"
    result = dirty_files(output)
    assert result == [" M file.py", "?? other.py"]
