# Benchmark Lifecycle

This document describes the end-to-end lifecycle of a benchmark run, from defining cases to acting on results.

---

## 1. Define Benchmark Cases

A benchmark case captures everything needed to evaluate a single retrieval event:

```json
{
  "id": "case-001",
  "query": {
    "id": "q-001",
    "text": "What are common symptoms of influenza?"
  },
  "context": [
    {
      "document": {
        "id": "doc-42",
        "content": "Influenza symptoms include fever, cough, fatigue ...",
        "metadata": {"source": "medical-wiki"}
      },
      "score": 0.92,
      "rank": 1
    }
  ],
  "relevant_doc_ids": ["doc-42", "doc-99"],
  "expected_answer": "Fever, cough, and fatigue are common flu symptoms."
}
```

Store cases in `fixtures/v1/<category>.json`. All fixtures must include a top-level
`format_version` and `category` key alongside the `cases` array.

---

## 2. Validate Fixtures

Before running a benchmark, validate your fixture to catch schema errors early:

```bash
python -m context_reliability_bench.validate_cli --fixture fixtures/v1/my_dataset.json
```

Or in Python:

```python
from pathlib import Path
from context_reliability_bench.validation import validate_benchmark_case
from context_reliability_bench.loader import load_fixture

cases = load_fixture(Path("fixtures/v1/my_dataset.json"))
for case in cases:
    validate_benchmark_case(case)
print(f"All {len(cases)} cases valid.")
```

---

## 3. Select Metrics

Choose from the five built-in metrics, all of which implement the `Metric` protocol:

| Class | Import | What it measures |
|-------|--------|-----------------|
| `PrecisionAtK(k=5)` | `metrics.precision_at_k` | Fraction of top-k results that are relevant |
| `RecallAtK(k=5)` | `metrics.recall_at_k` | Fraction of relevant docs found in top-k |
| `NdcgAtK(k=5)` | `metrics.ndcg` | Normalised Discounted Cumulative Gain |
| `ReciprocalRank()` | `metrics.mrr` | Mean Reciprocal Rank of the first relevant result |
| `TopKAccuracy(k=5)` | `metrics.top_k_accuracy` | Whether any relevant doc appears in top-k |

---

## 4. Run the Benchmark

```python
from pathlib import Path
from context_reliability_bench.loader import load_fixture
from context_reliability_bench.metrics.ndcg import NdcgAtK
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.metrics.recall_at_k import RecallAtK
from context_reliability_bench.runner import run_benchmark

cases = load_fixture(Path("fixtures/v1/noise_resistance.json"))
metrics: list[Metric] = [PrecisionAtK(k=5), RecallAtK(k=5), NdcgAtK(k=5)]
result = run_benchmark(cases, metrics, run_id="v1-noise-eval")
```

---

## 5. Analyse Results

```python
from context_reliability_bench.stats import run_stats
from context_reliability_bench.scoring import aggregate_score

print(f"Aggregate score: {aggregate_score(result):.4f}")
for stat in run_stats(result):
    print(
        f"{stat.metric_name}: "
        f"mean={stat.mean:.4f}  "
        f"min={stat.minimum:.4f}  "
        f"max={stat.maximum:.4f}  "
        f"std={stat.std_dev:.4f}"
    )
```

---

## 6. Export Reports

```python
from pathlib import Path
from context_reliability_bench.reports import (
    export_html,
    export_json,
    export_markdown,
)

export_html(result, Path("reports/result.html"))
export_markdown(result, Path("reports/result.md"))
export_json(result, Path("reports/result.json"))
```

---

## 7. Run Quality Gates (CI)

```python
import sys
from context_reliability_bench.quality_gates import (
    QualityGate,
    gates_exit_code,
    run_quality_gates,
)

gates = [
    QualityGate("precision@5", min_mean=0.60, description="P@5 must reach 60%"),
    QualityGate("recall@5",    min_mean=0.50, description="R@5 must reach 50%"),
    QualityGate("ndcg@5",      min_mean=0.55, description="NDCG@5 must reach 55%"),
]
report = run_quality_gates(result, gates)
for gr in report.gate_results:
    icon = "✓" if gr.passed else "✗"
    print(f"{icon} {gr.message}")

sys.exit(gates_exit_code(report))   # 0 = all pass, 1 = any fail
```

---

## 8. Track History and Detect Regressions

```python
from context_reliability_bench.history import BenchmarkHistory, BenchmarkRunRecord
from context_reliability_bench.regression import RegressionDetector

history = BenchmarkHistory(records=())
record = BenchmarkRunRecord(
    run_result=result,
    timestamp="2024-06-01T12:00:00",
    config_id="v1-noise-eval",
)
history = history.add_record(record)

# On the next run, check for regressions against the stored baseline:
detector = RegressionDetector(default_max_absolute_drop=0.05)
new_result = run_benchmark(cases, metrics, run_id="v1-noise-eval-2")
baseline = history.latest(1).records[0].run_result
regression_report = detector.detect(new_result, baseline)

if regression_report.has_regressions:
    for r in regression_report.detected():
        print(f"REGRESSION: {r.metric_name} — {r.reason}")
```

---

## 9. Analyse Trends

```python
from context_reliability_bench.trend import analyze_trends

history = history.add_record(
    BenchmarkRunRecord(
        run_result=new_result,
        timestamp="2024-06-08T12:00:00",
        config_id="v1-noise-eval",
    )
)

analysis = analyze_trends(history)
for trend in analysis.metric_trends:
    print(f"{trend.metric_name}: {trend.direction}  (slope={trend.slope:+.4f})")
```

---

## Lifecycle Summary

```
Define Cases  →  Validate  →  Select Metrics  →  Run Benchmark
                                                        │
                                                        ▼
                              Export Reports  ←  Analyse Results
                                                        │
                                                        ▼
                              Track History  →  Detect Regressions
                                    │
                                    ▼
                              Analyse Trends  →  Quality Gates  →  CI Exit
```
