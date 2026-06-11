"""Release validation script.

Runs every check that must pass before a release commit can be tagged:
  1. Ruff lint
  2. Mypy strict type check
  3. Full pytest suite
  4. Coverage threshold (>= 80 %)
  5. Build (wheel + sdist)
  6. Wheel installation smoke test (isolated venv)
  7. Version consistency across pyproject.toml, __version__, and CHANGELOG
  8. Repository cleanliness (no uncommitted changes)

Usage:
    python scripts/validate_release.py
    python scripts/validate_release.py --skip-build   # skip steps 5-6
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_PYTHON = sys.executable


def _run(label: str, cmd: list[str], **kwargs: object) -> bool:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=str(_ROOT), **kwargs)  # type: ignore[call-overload]
    if result.returncode != 0:
        print(f"\n[FAIL] {label}")
        return False
    print(f"\n[PASS] {label}")
    return True


def check_ruff() -> bool:
    return _run("Ruff lint", [_PYTHON, "-m", "ruff", "check", "."])


def check_mypy() -> bool:
    return _run("Mypy strict type check", [_PYTHON, "-m", "mypy", "."])


def check_pytest() -> bool:
    return _run("pytest suite", [_PYTHON, "-m", "pytest", "--tb=short", "-q"])


def check_coverage() -> bool:
    return _run(
        "Coverage (>= 80 %)",
        [
            _PYTHON, "-m", "pytest",
            "--cov=context_reliability_bench",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "-q",
        ],
    )


def check_build() -> bool:
    dist = _ROOT / "dist"
    if dist.exists():
        import shutil
        shutil.rmtree(dist)
    return _run("Build wheel + sdist", [_PYTHON, "-m", "build"])


def check_wheel_smoke() -> bool:
    return _run(
        "Wheel installation smoke test",
        [_PYTHON, str(_ROOT / "scripts" / "smoke_test_wheel.py")],
    )


def check_version_consistency() -> bool:
    print(f"\n{'='*60}")
    print("  Version consistency")
    print(f"{'='*60}")
    try:
        sys.path.insert(0, str(_ROOT / "src"))
        from context_reliability_bench.version_check import check_versions
        report = check_versions()
        for msg in report.messages:
            print(f"  {msg}")
        if report.consistent:
            print(f"\n[PASS] Version consistency — {report.sources.pyproject}")
            return True
        print("\n[FAIL] Version consistency")
        return False
    except Exception as exc:
        print(f"\n[FAIL] Version consistency — {exc}")
        return False


def check_repo_clean() -> bool:
    print(f"\n{'='*60}")
    print("  Repository cleanliness")
    print(f"{'='*60}")
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=str(_ROOT),
    )
    dirty = [
        line for line in result.stdout.splitlines()
        if not line.startswith("??")   # untracked files are OK
    ]
    if dirty:
        print("  Uncommitted changes:")
        for line in dirty:
            print(f"    {line}")
        print("\n[FAIL] Repository cleanliness")
        return False
    print("  Working tree clean")
    print("\n[PASS] Repository cleanliness")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-build", action="store_true",
        help="Skip build and wheel smoke-test steps",
    )
    args = parser.parse_args(argv)

    checks = [
        ("Ruff lint", check_ruff),
        ("Mypy", check_mypy),
        ("pytest", check_pytest),
        ("Coverage", check_coverage),
        ("Version consistency", check_version_consistency),
        ("Repository cleanliness", check_repo_clean),
    ]
    if not args.skip_build:
        checks.insert(4, ("Build", check_build))
        checks.insert(5, ("Wheel smoke test", check_wheel_smoke))

    results: list[tuple[str, bool]] = []
    for name, fn in checks:
        results.append((name, fn()))

    print(f"\n{'='*60}")
    print("  Release validation summary")
    print(f"{'='*60}")
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nAll checks passed. Repository is ready to tag a release.")
        return 0
    else:
        print("\nOne or more checks failed. Fix the issues above before tagging.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
