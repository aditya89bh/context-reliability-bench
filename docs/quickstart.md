# Quickstart Guide

Get up and running in five minutes.

---

## Step 1 — Install

```bash
git clone <repo-url>
cd context-reliability-bench
pip install -e ".[dev]"
```

Verify the install:

```bash
python -m context_reliability_bench --fixture fixtures/sample.json --k 5
```

You should see output like:

```
precision@5: 0.6667
recall@5: 0.6667
top_k_accuracy@5: 1.0000
mrr: 1.0000
ndcg@5: 0.7732
```

---

## Step 2 — Run your first benchmark

The library ships with a sample fixture at `fixtures/sample.json`. Use it to
verify everything works before pointing at your own data.

```python
from pathlib import Path
from context_reliability_bench.loader import load_fixture
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.runner import run_benchmark

# Load cases from a fixture file
cases = load_fixture(Path("fixtures/sample.json"))

# Select metrics
metrics: list[Metric] = [PrecisionAtK(k=5), RecallAtK(k=5)]

# Run
result = run_benchmark(cases, metrics, run_id="quickstart")

# Print results
for mr in result.metric_results:
    print(f"{mr.metric_name}: {mr.mean:.4f}")
```

---

## Step 3 — Export a report

```python
from context_reliability_bench.reports import export_html

from pathlib import Path

export_html(result, Path("report.html"))
print("Report written to report.html")
```

Open `report.html` in a browser to inspect per-case scores.

---

## Step 4 — Validate a fixture

Use the built-in CLI validator before running expensive evaluations:

```bash
python -m context_reliability_bench.validate_cli --fixture fixtures/sample.json
# OK: 3 case(s) validated
```

---

## Step 5 — Try a retriever adapter

Run the BM25 retriever against a set of labelled queries:

```python
from context_reliability_bench.retrieval import (
    BM25RetrieverAdapter,
    RetrievalQuery,
    run_retriever_benchmark,
)
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.models.document import Document

corpus = [
    Document(id="d1", content="Python is a high-level programming language"),
    Document(id="d2", content="Java is a compiled programming language"),
    Document(id="d3", content="SQL is used for database queries"),
]

retriever = BM25RetrieverAdapter()
retriever.index(corpus)

queries = [
    RetrievalQuery(
        id="q1",
        query_text="programming language",
        relevant_doc_ids=frozenset({"d1", "d2"}),
    ),
    RetrievalQuery(
        id="q2",
        query_text="database query language",
        relevant_doc_ids=frozenset({"d3"}),
    ),
]

metrics: list[Metric] = [PrecisionAtK(k=3)]
result = run_retriever_benchmark(retriever, queries, metrics)
print(f"BM25 Precision@3: {result.metric_results[0].mean:.4f}")
```

---

## Step 6 — Add quality gates

Assert minimum scores at the end of a CI job:

```python
import sys
from context_reliability_bench.quality_gates import (
    QualityGate,
    gates_exit_code,
    run_quality_gates,
)

gates = [QualityGate("precision@5", min_mean=0.50)]
report = run_quality_gates(result, gates)
sys.exit(gates_exit_code(report))   # exits 0 if passing, 1 if failing
```

---

## Next Steps

- Read [docs/benchmark_lifecycle.md](benchmark_lifecycle.md) for the full end-to-end lifecycle
- Follow [docs/tutorial.md](tutorial.md) for a step-by-step guide
- See [docs/cli_walkthrough.md](cli_walkthrough.md) for all CLI flags
- Browse [examples/](../examples/) for runnable scripts
