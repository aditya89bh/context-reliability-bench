"""Smoke tests for the installed package (importability, CLI, version).

These tests run against the current in-process installation, not a wheel,
so they are fast and require no build step.  The companion script
scripts/smoke_test_wheel.py tests a freshly built wheel in an isolated venv.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent


# ── import smoke tests ────────────────────────────────────────────────────────


def test_package_importable() -> None:
    import context_reliability_bench  # noqa: F401


def test_version_attribute_present() -> None:
    import context_reliability_bench
    assert hasattr(context_reliability_bench, "__version__")


def test_runner_importable() -> None:
    from context_reliability_bench.runner import run_benchmark  # noqa: F401


def test_loader_importable() -> None:
    from context_reliability_bench.loader import load_fixture  # noqa: F401


def test_metrics_importable() -> None:
    from context_reliability_bench.metrics.ndcg import NdcgAtK  # noqa: F401
    from context_reliability_bench.metrics.precision_at_k import (
        PrecisionAtK,  # noqa: F401
    )
    from context_reliability_bench.metrics.recall_at_k import RecallAtK  # noqa: F401


def test_retrieval_importable() -> None:
    from context_reliability_bench.retrieval import (  # noqa: F401
        BM25RetrieverAdapter,
        InMemoryRetrieverAdapter,
        VectorRetrieverAdapter,
    )


def test_quality_gates_importable() -> None:
    from context_reliability_bench.quality_gates import (  # noqa: F401
        QualityGate,
        gates_exit_code,
        run_quality_gates,
    )


def test_cache_importable() -> None:
    from context_reliability_bench.cache import BenchmarkCache  # noqa: F401


def test_parallel_importable() -> None:
    from context_reliability_bench.parallel import run_parallel  # noqa: F401


def test_reproducibility_importable() -> None:
    from context_reliability_bench.reproducibility import (  # noqa: F401
        capture_metadata,
    )


def test_timing_importable() -> None:
    from context_reliability_bench.timing import BenchmarkTiming  # noqa: F401


# ── CLI smoke test ────────────────────────────────────────────────────────────


def test_cli_help_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "context_reliability_bench", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_validate_cli_help_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "context_reliability_bench.validate_cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_validate_cli_on_sample_fixture() -> None:
    fixture = _ROOT / "fixtures" / "sample.json"
    result = subprocess.run(
        [sys.executable, "-m", "context_reliability_bench.validate_cli",
         "--fixture", str(fixture)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "OK" in result.stdout


# ── version consistency ───────────────────────────────────────────────────────


def test_installed_version_consistent() -> None:
    from context_reliability_bench.version_check import check_versions
    report = check_versions()
    assert report.consistent, "\n".join(report.messages)


def test_installed_version_matches_pyproject() -> None:
    import re

    import context_reliability_bench
    text = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert m is not None
    assert context_reliability_bench.__version__ == m.group(1)
