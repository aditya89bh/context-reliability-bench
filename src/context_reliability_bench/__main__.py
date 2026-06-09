from __future__ import annotations

import argparse
import sys
from pathlib import Path

from context_reliability_bench.loader import FixtureError, load_fixture
from context_reliability_bench.metrics.mrr import ReciprocalRank
from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.metrics.top_k_accuracy import TopKAccuracy
from context_reliability_bench.reports.csv_export import export_csv
from context_reliability_bench.reports.json_export import export_json
from context_reliability_bench.runner import run_benchmark


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="context-reliability-bench",
        description="Run a context retrieval benchmark.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        required=True,
        help="Path to the benchmark fixture JSON file.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="K for rank-based metrics (default: 5).",
    )
    parser.add_argument(
        "--run-id",
        default="default",
        help="Identifier for this run (default: 'default').",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write JSON report to PATH.",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write CSV report to PATH.",
    )

    args = parser.parse_args(argv)
    k: int = args.k

    try:
        cases = load_fixture(args.fixture)
    except FixtureError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    metrics: list[Metric] = [
        PrecisionAtK(k=k),
        RecallAtK(k=k),
        TopKAccuracy(k=k),
        ReciprocalRank(),
        NdcgAtK(k=k),
    ]

    result = run_benchmark(cases, metrics, run_id=args.run_id)

    for mr in result.metric_results:
        print(f"{mr.metric_name}: {mr.mean:.4f}")

    if args.json_out is not None:
        export_json(result, args.json_out)
        print(f"JSON report written to {args.json_out}")

    if args.csv_out is not None:
        export_csv(result, args.csv_out)
        print(f"CSV report written to {args.csv_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
