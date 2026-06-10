"""
Retriever benchmark example.

Run with:
    python examples/retriever_benchmark.py

Demonstrates: indexing a corpus, running BM25 and in-memory retrievers,
comparing their results side-by-side, and detecting regressions.
"""

from __future__ import annotations

import sys
from pathlib import Path

from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.models.document import Document
from context_reliability_bench.regression import RegressionDetector
from context_reliability_bench.retrieval import (
    BM25RetrieverAdapter,
    InMemoryRetrieverAdapter,
    RetrievalQuery,
    run_retriever_benchmark,
)

_ROOT = Path(__file__).parent.parent

# ── Sample corpus ──────────────────────────────────────────────────────────────
_CORPUS = [
    Document(
        id="d1",
        content="Python is a high-level general-purpose programming language.",
        metadata={"topic": "programming"},
    ),
    Document(
        id="d2",
        content="Java is a compiled object-oriented programming language.",
        metadata={"topic": "programming"},
    ),
    Document(
        id="d3",
        content="SQL is the standard language for relational database queries.",
        metadata={"topic": "database"},
    ),
    Document(
        id="d4",
        content="Machine learning models learn patterns from training data.",
        metadata={"topic": "ml"},
    ),
    Document(
        id="d5",
        content="Neural networks are a class of machine learning models.",
        metadata={"topic": "ml"},
    ),
]

# ── Labelled queries ───────────────────────────────────────────────────────────
_QUERIES = [
    RetrievalQuery(
        id="q1",
        query_text="programming language",
        relevant_doc_ids=frozenset({"d1", "d2"}),
    ),
    RetrievalQuery(
        id="q2",
        query_text="database query SQL",
        relevant_doc_ids=frozenset({"d3"}),
    ),
    RetrievalQuery(
        id="q3",
        query_text="machine learning neural network",
        relevant_doc_ids=frozenset({"d4", "d5"}),
    ),
]


def _run_retriever(name: str, metrics: list[Metric]) -> None:
    retriever = (
        BM25RetrieverAdapter() if name == "bm25" else InMemoryRetrieverAdapter()
    )

    retriever.index(_CORPUS)
    result = run_retriever_benchmark(retriever, _QUERIES, metrics, top_k=5)

    print(f"\n── {name.upper()} Retriever ──────────────────────────")
    for mr in result.metric_results:
        scores_str = ", ".join(f"{s:.3f}" for _, s in mr.case_scores)
        print(f"  {mr.metric_name:<14} mean={mr.mean:.4f}  per-query=[{scores_str}]")


def main() -> int:
    print("=== Retriever Benchmark Example ===\n")
    print(f"Corpus: {len(_CORPUS)} documents")
    print(f"Queries: {len(_QUERIES)} labelled queries\n")

    k = 5
    metrics: list[Metric] = [PrecisionAtK(k=k), RecallAtK(k=k), NdcgAtK(k=k)]

    _run_retriever("in_memory", metrics)
    _run_retriever("bm25", metrics)

    # ── Regression check: compare BM25 vs in-memory as "baseline" ─────────────
    print("\n── Regression Check (BM25 vs InMemory baseline) ──")
    baseline_retriever = InMemoryRetrieverAdapter()
    baseline_retriever.index(_CORPUS)
    baseline = run_retriever_benchmark(
        baseline_retriever, _QUERIES, metrics, top_k=k
    )

    candidate_retriever = BM25RetrieverAdapter()
    candidate_retriever.index(_CORPUS)
    candidate = run_retriever_benchmark(
        candidate_retriever, _QUERIES, metrics, top_k=k
    )

    detector = RegressionDetector(default_max_absolute_drop=0.30)
    report = detector.detect(candidate, baseline)

    if report.has_regressions:
        for r in report.detected():
            print(f"  REGRESSION: {r.metric_name} — {r.reason}")
    else:
        print("  No regressions detected.")

    # ── Export results ─────────────────────────────────────────────────────────
    out_dir = _ROOT / "examples" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    from context_reliability_bench.reports import export_json

    export_json(candidate, out_dir / "retriever_result.json")
    print(f"\nResult written to {out_dir}/retriever_result.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
