# Benchmark Tutorial

A step-by-step guide to building a complete retrieval quality evaluation pipeline.

---

## What We'll Build

By the end of this tutorial you will have:

1. A validated benchmark fixture
2. A retriever evaluated on five metrics
3. HTML and JSON reports exported
4. A quality gate that fails the CI when precision drops below a threshold
5. Regression detection against a stored baseline

Estimated time: 20 minutes.

---

## Prerequisites

```bash
git clone <repo-url>
cd context-reliability-bench
pip install -e ".[dev]"
```

---

## Part 1 — Define Your Benchmark Cases

A benchmark case links a query to a set of retrieved documents and the ground-truth
relevant document IDs.

Create `fixtures/v1/my_dataset.json`:

```json
{
  "format_version": "1.0",
  "category": "my_dataset",
  "cases": [
    {
      "id": "case-001",
      "query": { "id": "q-001", "text": "What is machine learning?" },
      "context": [
        {
          "document": {
            "id": "doc-ml-intro",
            "content": "Machine learning is a subfield of AI ...",
            "metadata": {}
          },
          "score": 0.95,
          "rank": 1
        },
        {
          "document": {
            "id": "doc-dl-intro",
            "content": "Deep learning uses neural networks ...",
            "metadata": {}
          },
          "score": 0.82,
          "rank": 2
        }
      ],
      "relevant_doc_ids": ["doc-ml-intro"],
      "expected_answer": "Machine learning is a subfield of AI that enables systems to learn."
    }
  ]
}
```

### Validate the fixture

```bash
python -m context_reliability_bench.validate_cli --fixture fixtures/v1/my_dataset.json
# OK: 1 case(s) validated
```

---

## Part 2 — Run the Benchmark

```python
from pathlib import Path
from context_reliability_bench.loader import load_fixture
from context_reliability_bench.metrics.mrr import ReciprocalRank
from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.metrics.top_k_accuracy import TopKAccuracy
from context_reliability_bench.runner import run_benchmark

cases = load_fixture(Path("fixtures/v1/my_dataset.json"))

k = 5
metrics: list[Metric] = [
    PrecisionAtK(k=k),
    RecallAtK(k=k),
    NdcgAtK(k=k),
    ReciprocalRank(),
    TopKAccuracy(k=k),
]

result = run_benchmark(cases, metrics, run_id="tutorial-run-1")

for mr in result.metric_results:
    print(f"{mr.metric_name}: {mr.mean:.4f}")
```

---

## Part 3 — Evaluate a Live Retriever

Instead of pre-computed context, let your retriever fetch documents at evaluation time.

```python
from context_reliability_bench.retrieval import (
    BM25RetrieverAdapter,
    RetrievalQuery,
    run_retriever_benchmark,
)
from context_reliability_bench.models.document import Document

# Build a corpus
corpus = [
    Document(id="doc-ml-intro",  content="Machine learning is a subfield of AI ..."),
    Document(id="doc-dl-intro",  content="Deep learning uses neural networks ..."),
    Document(id="doc-nlp-intro", content="NLP processes human language with AI ..."),
]

# Index the corpus
retriever = BM25RetrieverAdapter()
retriever.index(corpus)

# Define evaluation queries with ground truth
queries = [
    RetrievalQuery(
        id="q1",
        query_text="machine learning AI",
        relevant_doc_ids=frozenset({"doc-ml-intro"}),
    ),
    RetrievalQuery(
        id="q2",
        query_text="neural network deep learning",
        relevant_doc_ids=frozenset({"doc-dl-intro"}),
    ),
]

result = run_retriever_benchmark(retriever, queries, metrics, top_k=k)
for mr in result.metric_results:
    print(f"{mr.metric_name}: {mr.mean:.4f}")
```

---

## Part 4 — Export Reports

```python
from pathlib import Path
from context_reliability_bench.reports import export_html, export_json, export_markdown

Path("reports").mkdir(exist_ok=True)
export_html(result, Path("reports/report.html"))
export_markdown(result, Path("reports/report.md"))
export_json(result, Path("reports/report.json"))
```

Open `reports/report.html` to inspect per-case scores in a browser.

---

## Part 5 — Add Quality Gates (CI)

Add a step at the end of your CI pipeline:

```python
import sys
from context_reliability_bench.quality_gates import (
    QualityGate,
    gates_exit_code,
    run_quality_gates,
)

gates = [
    QualityGate(f"precision@{k}", min_mean=0.60, description="P@K must be ≥ 60%"),
    QualityGate(f"recall@{k}",    min_mean=0.50, description="R@K must be ≥ 50%"),
    QualityGate(f"ndcg@{k}",      min_mean=0.55, description="NDCG@K must be ≥ 55%"),
]

gate_report = run_quality_gates(result, gates)
for gr in gate_report.gate_results:
    status = "PASS" if gr.passed else "FAIL"
    print(f"[{status}] {gr.message}")

# Returns 0 (success) or 1 (failure) — suitable for sys.exit()
code = gates_exit_code(gate_report)
print(f"\nCI exit code: {code}")
sys.exit(code)
```

---

## Part 6 — Track History and Detect Regressions

```python
from context_reliability_bench.history import BenchmarkHistory, BenchmarkRunRecord
from context_reliability_bench.regression import RegressionDetector

# Store this run
history = BenchmarkHistory(records=())
record = BenchmarkRunRecord(
    run_result=result,
    timestamp="2024-06-01T12:00:00",
    config_id="bm25-tutorial",
)
history = history.add_record(record)

# On a subsequent run, detect regressions
next_result = run_retriever_benchmark(retriever, queries, metrics, top_k=k)
baseline = history.latest(1).records[0].run_result

detector = RegressionDetector(default_max_absolute_drop=0.05)
reg_report = detector.detect(next_result, baseline)

if reg_report.has_regressions:
    for r in reg_report.detected():
        print(f"REGRESSION in {r.metric_name}: {r.reason}")
else:
    print("No regressions detected.")
```

---

## Part 7 — Analyse Trends

```python
from context_reliability_bench.trend import analyze_trends

analysis = analyze_trends(history)
for trend in analysis.metric_trends:
    print(f"{trend.metric_name}: {trend.direction}  slope={trend.slope:+.4f}")
```

---

## Part 8 — Use YAML Configuration

Save your configuration in a `.yaml` file:

```yaml
# bench.yaml
fixture_path: fixtures/v1/my_dataset.json
run_id: tutorial-ci
k: 5
metric_names:
  - precision
  - recall
  - ndcg
tags:
  - ci
  - tutorial
```

Load and run:

```python
from pathlib import Path
from context_reliability_bench.config import load_yaml_config
from context_reliability_bench.batch import run_batch

config = load_yaml_config(Path("bench.yaml"))
batch_result = run_batch([config])
run = batch_result.results[0]
print(f"Ran '{run.run_id}': {len(run.metric_results)} metrics")
```

---

## Summary

You now know how to:

| Task | Module |
|------|--------|
| Load and validate fixtures | `loader`, `validation` |
| Run metrics against fixed context | `runner` |
| Evaluate a live retriever | `retrieval.harness` |
| Export HTML/JSON/Markdown reports | `reports` |
| Enforce CI quality gates | `quality_gates` |
| Track run history | `history` |
| Detect metric regressions | `regression` |
| Analyse performance trends | `trend` |
| Configure via YAML | `config.yaml_config` |

See [examples/](../examples/) for complete runnable scripts.
