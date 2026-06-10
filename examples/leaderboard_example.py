"""
Leaderboard example.

Run with:
    python examples/leaderboard_example.py

Demonstrates: running the same fixture with different retriever configurations,
building a leaderboard, ranking entries by metric, and exporting to JSON/CSV.
"""

from __future__ import annotations

import sys
from pathlib import Path

from context_reliability_bench.leaderboard_export import (
    build_leaderboard_entry,
    export_leaderboard_csv,
    export_leaderboard_json,
)
from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.models.document import Document
from context_reliability_bench.models.leaderboard import Leaderboard, LeaderboardEntry
from context_reliability_bench.retrieval import (
    BM25RetrieverAdapter,
    InMemoryRetrieverAdapter,
    RetrievalQuery,
    VectorRetrieverAdapter,
    run_retriever_benchmark,
)
from context_reliability_bench.retrieval.vector import VectorBackend

_ROOT = Path(__file__).parent.parent
_OUT = _ROOT / "examples" / "output"

# ── Shared corpus and queries ──────────────────────────────────────────────────

_CORPUS = [
    Document(id="d1", content="Python programming language high level"),
    Document(id="d2", content="Java object oriented compiled language"),
    Document(id="d3", content="SQL relational database query language"),
    Document(id="d4", content="machine learning artificial intelligence models"),
    Document(id="d5", content="deep learning neural network training"),
    Document(id="d6", content="natural language processing text analysis"),
]

_QUERIES = [
    RetrievalQuery(
        id="q1",
        query_text="programming language Python Java",
        relevant_doc_ids=frozenset({"d1", "d2"}),
    ),
    RetrievalQuery(
        id="q2",
        query_text="database SQL query",
        relevant_doc_ids=frozenset({"d3"}),
    ),
    RetrievalQuery(
        id="q3",
        query_text="neural network deep learning",
        relevant_doc_ids=frozenset({"d4", "d5"}),
    ),
    RetrievalQuery(
        id="q4",
        query_text="natural language text NLP",
        relevant_doc_ids=frozenset({"d6"}),
    ),
]


# ── Minimal vector backend for leaderboard demo ───────────────────────────────


class _TFBackend:
    """Term-frequency VectorBackend (no external deps)."""

    def __init__(self) -> None:
        self._docs: dict[str, str] = {}

    def add(self, doc_id: str, text: str) -> None:
        self._docs[doc_id] = text

    def search(self, query_text: str, top_k: int) -> list[tuple[str, float]]:
        terms = query_text.lower().split()
        scored = [
            (
                doc_id,
                sum(t in text.lower() for t in terms) / max(len(terms), 1),
            )
            for doc_id, text in self._docs.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(doc_id, float(s)) for doc_id, s in scored[:top_k]]


assert isinstance(_TFBackend(), VectorBackend)


def _make_leaderboard_entry(
    system_name: str,
    metrics: list[Metric],
    top_k: int,
) -> LeaderboardEntry:
    if system_name == "BM25":
        retriever = BM25RetrieverAdapter()
    elif system_name == "TF-Vector":
        retriever = VectorRetrieverAdapter(_TFBackend(), name="tf_vector")
    else:
        retriever = InMemoryRetrieverAdapter()

    retriever.index(_CORPUS)
    result = run_retriever_benchmark(retriever, _QUERIES, metrics, top_k=top_k)
    return build_leaderboard_entry(result, system_name=system_name)


def main() -> int:
    print("=== Leaderboard Example ===\n")

    k = 5
    metrics: list[Metric] = [PrecisionAtK(k=k), RecallAtK(k=k), NdcgAtK(k=k)]
    systems = ["InMemory", "BM25", "TF-Vector"]

    # ── Build leaderboard ──────────────────────────────────────────────────────
    leaderboard = Leaderboard(benchmark_name="retrieval-benchmark", entries=())
    for system in systems:
        entry = _make_leaderboard_entry(system, metrics, top_k=k)
        leaderboard = leaderboard.add_entry(entry)
        print(f"  Added: {system}")

    # ── Print rankings ─────────────────────────────────────────────────────────
    rank_metric = f"ndcg@{k}"
    print(f"\n── Rankings by {rank_metric} ──────────────────────────")
    for rank, entry in enumerate(leaderboard.ranked_by(rank_metric), start=1):
        score = entry.get_score(rank_metric)
        score_str = f"{score:.4f}" if score is not None else "N/A"
        print(f"  #{rank}  {entry.system_name:<14} {rank_metric}={score_str}")

    # ── Export ─────────────────────────────────────────────────────────────────
    _OUT.mkdir(parents=True, exist_ok=True)
    json_path = _OUT / "leaderboard.json"
    csv_path = _OUT / "leaderboard.csv"
    export_leaderboard_json(leaderboard, json_path)
    export_leaderboard_csv(leaderboard, csv_path)

    print(f"\nLeaderboard JSON → {json_path.relative_to(_ROOT)}")
    print(f"Leaderboard CSV  → {csv_path.relative_to(_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
