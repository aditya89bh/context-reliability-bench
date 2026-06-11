"""Smoke-test a built wheel by installing it into a fresh venv and importing it.

Usage:
    python scripts/smoke_test_wheel.py          # auto-discovers dist/*.whl
    python scripts/smoke_test_wheel.py dist/context_reliability_bench-*.whl
"""

from __future__ import annotations

import glob
import subprocess
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).parent.parent


def _find_wheel() -> Path:
    pattern = str(_ROOT / "dist" / "*.whl")
    candidates = sorted(glob.glob(pattern))
    if not candidates:
        raise FileNotFoundError(
            f"No wheel found matching {pattern}. "
            "Run `python -m build` first."
        )
    return Path(candidates[-1])


def _run(cmd: list[str], **kwargs: object) -> None:
    result = subprocess.run(cmd, check=True, **kwargs)  # type: ignore[call-overload]
    _ = result  # silence unused-variable lint


def smoke_test(wheel: Path) -> None:
    print(f"Smoke-testing wheel: {wheel.name}")
    with tempfile.TemporaryDirectory(prefix="crb-smoke-") as tmpdir:
        venv = Path(tmpdir) / "venv"

        print("  Creating isolated venv …")
        _run([sys.executable, "-m", "venv", str(venv)])

        python = venv / "bin" / "python"
        pip = venv / "bin" / "pip"

        print("  Installing wheel …")
        _run([str(pip), "install", "--quiet", str(wheel)])

        print("  Verifying import …")
        _run([str(python), "-c",
              "import context_reliability_bench; "
              "print('version:', context_reliability_bench.__version__)"])

        print("  Verifying submodule imports …")
        _run([str(python), "-c", (
            "from context_reliability_bench.runner import run_benchmark; "
            "from context_reliability_bench.loader import load_fixture; "
            "from context_reliability_bench.metrics.precision_at_k"
            " import PrecisionAtK; "
            "from context_reliability_bench.retrieval import BM25RetrieverAdapter; "
            "from context_reliability_bench.quality_gates import run_quality_gates; "
            "print('all submodule imports OK')"
        )])

        print("  Verifying CLI entry point …")
        _run([str(python), "-m", "context_reliability_bench", "--help"],
             capture_output=True)

        print("  Verifying version consistency …")
        _run([str(python), "-c", (
            "from context_reliability_bench.version_check import check_versions; "
            "r = check_versions(); "
            "assert r.consistent, r.messages; "
            "print('version consistent:', r.sources.pyproject)"
        )])

    print(f"Smoke test PASSED for {wheel.name}")


def main() -> int:
    wheel_path = Path(sys.argv[1]) if len(sys.argv) > 1 else _find_wheel()
    try:
        smoke_test(wheel_path)
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
