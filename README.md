# context-reliability-bench

A Python library for benchmarking the retrieval quality of RAG (Retrieval-Augmented Generation) systems. Measure precision, recall, NDCG, MRR, and top-k accuracy against ground-truth relevance labels — with pluggable retrievers, report generation, trend analysis, and CI quality gates.

---

## Features

- **Five standard retrieval metrics** — Precision@K, Recall@K, NDCG@K, MRR, Top-K Accuracy
- **Pluggable retriever adapters** — in-memory, BM25 (pure Python, zero extra deps), and a `VectorBackend` protocol for any embedding store
- **Versioned fixture datasets** — JSON benchmark cases with manifest-based discovery
- **Multi-category suite runner** — Noise Resistance, Contradiction, Temporal Relevance, Distractor categories out of the box
- **Rich report formats** — HTML, Markdown, JSON, CSV, leaderboard, and dashboard exports
- **Run history & trend analysis** — track metrics over time, detect degrading slopes
- **Regression detection** — configurable absolute and relative drop thresholds per metric
- **Quality gates** — assert minimum metric scores; returns a CI-compatible exit code
- **YAML configuration** — load benchmark settings from `.yaml` files with no extra dependencies
- **Execution profiles** — `QUICK`, `STANDARD`, and `THOROUGH` preset configurations

---

## Installation

```bash
git clone <repo-url>
cd context-reliability-bench
pip install -e ".[dev]"
```

---

## Quick Start

### Evaluate a fixture file

```python
from pathlib import Path
from context_reliability_bench.loader import load_fixture
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.runner import run_benchmark

cases = load_fixture(Path("fixtures/sample.json"))
metrics: list[Metric] = [PrecisionAtK(k=5), RecallAtK(k=5)]
result = run_benchmark(cases, metrics, run_id="my-run")

for mr in result.metric_results:
    print(f"{mr.metric_name}: {mr.mean:.4f}")
```

### Run via CLI

```bash
python -m context_reliability_bench \
    --fixture fixtures/sample.json \
    --k 5 \
    --run-id ci-run \
    --json-out results.json
```

---

## Retriever Adapters

Plug in any retriever to evaluate it against labelled queries:

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
    Document(id="d1", content="cats are common household pets"),
    Document(id="d2", content="dogs need daily walks"),
]
retriever = BM25RetrieverAdapter()
retriever.index(corpus)

queries = [
    RetrievalQuery(
        id="q1",
        query_text="cat pet",
        relevant_doc_ids=frozenset({"d1"}),
    ),
]
metrics: list[Metric] = [PrecisionAtK(k=5)]
result = run_retriever_benchmark(retriever, queries, metrics)
print(result.metric_results[0].mean)
```

---

## Quality Gates for CI

```python
import sys
from context_reliability_bench.quality_gates import (
    QualityGate,
    gates_exit_code,
    run_quality_gates,
)

gates = [
    QualityGate("precision@5", min_mean=0.60),
    QualityGate("recall@5",    min_mean=0.50),
]
report = run_quality_gates(result, gates)
for gr in report.gate_results:
    status = "PASS" if gr.passed else "FAIL"
    print(f"[{status}] {gr.message}")

sys.exit(gates_exit_code(report))
```

---

## Report Exports

```python
from pathlib import Path
from context_reliability_bench.reports import export_html, export_json, export_markdown

export_html(result, Path("report.html"))
export_markdown(result, Path("report.md"))
export_json(result, Path("report.json"))
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/quickstart.md](docs/quickstart.md) | Five-minute guide |
| [docs/benchmark_lifecycle.md](docs/benchmark_lifecycle.md) | End-to-end lifecycle |
| [docs/tutorial.md](docs/tutorial.md) | Full step-by-step tutorial |
| [docs/cli_walkthrough.md](docs/cli_walkthrough.md) | CLI reference |
| [docs/index.md](docs/index.md) | Documentation hub |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

---

## Examples

| File | Description |
|------|-------------|
| [examples/basic_benchmark.py](examples/basic_benchmark.py) | Run a benchmark end-to-end |
| [examples/retriever_benchmark.py](examples/retriever_benchmark.py) | Evaluate a BM25 retriever |
| [examples/langchain_integration.py](examples/langchain_integration.py) | LangChain adapter pattern |
| [examples/llamaindex_integration.py](examples/llamaindex_integration.py) | LlamaIndex adapter pattern |
| [examples/generate_reports.py](examples/generate_reports.py) | Export HTML/Markdown/JSON reports |
| [examples/leaderboard_example.py](examples/leaderboard_example.py) | Build and export a leaderboard |

---

## License

MIT
