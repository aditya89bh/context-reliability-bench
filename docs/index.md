# context-reliability-bench Documentation

Welcome to the documentation hub for `context-reliability-bench` — a Python
library for evaluating retrieval quality in RAG and information-retrieval systems.

---

## Getting Started

| Step | Resource |
|------|----------|
| Install and first run | [Quickstart](quickstart.md) |
| Full walkthrough | [Tutorial](tutorial.md) |
| CLI flags and CI integration | [CLI Walkthrough](cli_walkthrough.md) |

---

## Core Concepts

### Benchmark Cases

A **benchmark case** links a natural-language query to a list of retrieved
documents and a set of ground-truth relevant document IDs.  Cases are stored in
JSON fixtures and loaded with `load_fixture`.

```python
from pathlib import Path
from context_reliability_bench.loader import load_fixture

cases = load_fixture(Path("fixtures/sample.json"))
```

### Metrics

Metrics implement `compute(context, relevant_doc_ids) -> float` and return a
score in `[0.0, 1.0]`.

| Class | Module | What it measures |
|-------|--------|-----------------|
| `PrecisionAtK` | `metrics.precision_at_k` | Fraction of top-K that are relevant |
| `RecallAtK` | `metrics.recall_at_k` | Fraction of relevant docs in top-K |
| `NdcgAtK` | `metrics.ndcg` | Ranking quality, penalises lower positions |
| `ReciprocalRank` | `metrics.mrr` | Position of the first relevant result |
| `TopKAccuracy` | `metrics.top_k_accuracy` | Whether any relevant doc is in top-K |

### Run Results

`run_benchmark` returns a `RunResult` containing one `MetricResult` per metric.
Each `MetricResult` exposes `mean`, `std_dev`, `min`, `max`, and per-case scores.

---

## Retrieval Adapters

Evaluate a **live retriever** instead of pre-computed context:

```python
from context_reliability_bench.retrieval import (
    BM25RetrieverAdapter,
    RetrievalQuery,
    run_retriever_benchmark,
)
```

Built-in adapters:

| Adapter | Description |
|---------|-------------|
| `InMemoryRetrieverAdapter` | Term-overlap scorer, no external deps |
| `BM25RetrieverAdapter` | BM25 (k1=1.5, b=0.75), no external deps |
| `VectorRetrieverAdapter` | Wraps any `VectorBackend` implementation |

Plug in any retrieval system by implementing the `RetrieverAdapter` protocol
(three methods: `name`, `index`, `retrieve`).

---

## Configuration

### Python

```python
from context_reliability_bench.config import BenchmarkConfig, ExecutionProfile, config_from_profile

config = config_from_profile("fixtures/sample.json", ExecutionProfile.STANDARD)
```

### YAML

```yaml
fixture_path: fixtures/v1/noise_resistance.json
run_id: nightly
k: 5
metric_names: [precision, recall, ndcg]
tags: [ci, nightly]
```

```python
from context_reliability_bench.config import load_yaml_config
config = load_yaml_config(Path("bench.yaml"))
```

---

## CI Integration

### Quality Gates

Fail your CI pipeline if a metric drops below a threshold:

```python
from context_reliability_bench.quality_gates import (
    QualityGate, run_quality_gates, gates_exit_code
)
gates = [QualityGate("precision@5", min_mean=0.60)]
report = run_quality_gates(result, gates)
sys.exit(gates_exit_code(report))   # 0 = pass, 1 = fail
```

### Regression Detection

```python
from context_reliability_bench.regression import RegressionDetector
detector = RegressionDetector(default_max_absolute_drop=0.05)
reg_report = detector.detect(current_result, baseline_result)
```

See [CLI Walkthrough → Common CI patterns](cli_walkthrough.md#3-common-ci-patterns) for
a complete pipeline example.

---

## Analysis

| API | Purpose |
|-----|---------|
| `BenchmarkHistory` | Store and filter past runs |
| `BenchmarkComparisonEngine` | Compare two run results |
| `analyze_trends` | Linear trend and direction over history |
| `run_batch` | Execute multiple configs in one call |

---

## Reports and Exports

```python
from context_reliability_bench.reports import (
    export_html, export_markdown, export_json, export_csv,
    export_dashboard_json, export_comparison_json,
)
```

| Format | Function |
|--------|----------|
| HTML | `export_html(result, path)` |
| Markdown | `export_markdown(result, path)` |
| JSON | `export_json(result, path)` |
| CSV | `export_csv(result, path)` |
| Dashboard JSON | `export_dashboard_json(suite_result, path)` |

---

## Diagrams

Architecture diagrams live in [`docs/assets/architecture.md`](assets/architecture.md):

- Component overview (layered view)
- Data flow chart
- Module dependency map

---

## Full Documentation Map

| Document | Purpose |
|----------|---------|
| [README](../README.md) | Project overview and feature list |
| [Quickstart](quickstart.md) | Install and first benchmark in 10 minutes |
| [Tutorial](tutorial.md) | Step-by-step: fixture → metrics → CI |
| [Benchmark Lifecycle](benchmark_lifecycle.md) | 9-step lifecycle reference |
| [CLI Walkthrough](cli_walkthrough.md) | All flags, examples, exit codes |
| [Architecture](assets/architecture.md) | Component and data flow diagrams |
| [CONTRIBUTING](../CONTRIBUTING.md) | Dev setup, standards, extension guides |
| [CHANGELOG](../CHANGELOG.md) | Release history |

---

## Examples

All examples under `examples/` execute without external dependencies.

| Script | Demonstrates |
|--------|--------------|
| `basic_benchmark.py` | Fixture → metrics → gates → JSON/MD reports |
| `retriever_benchmark.py` | BM25 vs InMemory comparison + regression check |
| `langchain_integration.py` | `VectorBackend` adapter pattern for LangChain |
| `llamaindex_integration.py` | `RetrieverAdapter` bridge for LlamaIndex |
| `generate_reports.py` | HTML/Markdown/JSON/CSV/dashboard export |
| `leaderboard_example.py` | Multi-system leaderboard with rankings |

Run any example:

```bash
python examples/basic_benchmark.py
```

---

## Package Structure

```
src/context_reliability_bench/
├── models/            ← Document, Query, RetrievedContext, BenchmarkCase
├── metrics/           ← PrecisionAtK, RecallAtK, NdcgAtK, MRR, TopKAccuracy
├── retrieval/         ← InMemory, BM25, Vector adapters + harness
├── config/            ← BenchmarkConfig, YAML loader, execution profiles
├── reports/           ← HTML, Markdown, JSON, CSV, dashboard exporters
├── categories/        ← Built-in benchmark category implementations
├── runner.py          ← run_benchmark
├── batch.py           ← run_batch
├── history.py         ← BenchmarkHistory
├── comparison_engine.py ← BenchmarkComparisonEngine
├── trend.py           ← analyze_trends
├── regression.py      ← RegressionDetector
├── quality_gates.py   ← run_quality_gates, gates_exit_code
└── suite.py           ← build_default_registry, run_suite
```
