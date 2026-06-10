from __future__ import annotations

import argparse
import sys
from pathlib import Path

from context_reliability_bench.loader import FixtureError, load_fixture
from context_reliability_bench.validation import (
    ValidationError,
    validate_benchmark_case,
)


def validate_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate-dataset",
        description="Validate a benchmark fixture JSON file.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        required=True,
        metavar="PATH",
        help="Path to the fixture JSON file to validate.",
    )
    args = parser.parse_args(argv)

    try:
        cases = load_fixture(args.fixture)
    except FixtureError as exc:
        print(f"Error loading fixture: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for i, case in enumerate(cases):
        try:
            validate_benchmark_case(case)
        except ValidationError as exc:
            errors.append(f"  cases[{i}] ({case.id}): {exc}")

    if errors:
        print(f"Validation failed ({args.fixture}):", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(f"OK: {len(cases)} case(s) validated in {args.fixture}")
    return 0


if __name__ == "__main__":
    sys.exit(validate_main())
