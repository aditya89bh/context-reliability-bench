# CLI Walkthrough

`context-reliability-bench` ships two command-line entry points.

---

## 1. Benchmark runner

```
python -m context_reliability_bench [OPTIONS]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--fixture PATH` | *(required)* | Path to the benchmark fixture JSON file |
| `--k K` | `5` | K for rank-based metrics (Precision@K, Recall@K, NDCG@K, Top-K Accuracy) |
| `--run-id RUN_ID` | `"default"` | Label for this run (appears in all export files) |
| `--json-out PATH` | *(none)* | Write a JSON report to `PATH` |
| `--csv-out PATH` | *(none)* | Write a CSV report to `PATH` |

### Examples

**Minimal run — print results to stdout:**

```bash
python -m context_reliability_bench --fixture fixtures/sample.json
```

Sample output:

```
precision@5: 0.2000
recall@5: 1.0000
top5_accuracy: 1.0000
reciprocal_rank: 1.0000
ndcg@5: 1.0000
```

**Custom k and labelled run:**

```bash
python -m context_reliability_bench \
    --fixture fixtures/v1/noise_resistance.json \
    --k 10 \
    --run-id nightly-eval
```

**Export JSON and CSV reports:**

```bash
python -m context_reliability_bench \
    --fixture fixtures/sample.json \
    --run-id ci-run \
    --json-out results/report.json \
    --csv-out results/report.csv
```

**Use inside a CI pipeline (exit code reflects success/failure):**

```bash
python -m context_reliability_bench \
    --fixture fixtures/v1/noise_resistance.json \
    --k 5 \
    --json-out /tmp/bench.json
```

The CLI always exits with code `0`.  To fail CI on low metric scores, use
the Python API with `run_quality_gates` + `gates_exit_code`.

---

## 2. Fixture validator

```
python -m context_reliability_bench.validate_cli --fixture PATH
```

### Options

| Flag | Description |
|------|-------------|
| `--fixture PATH` | *(required)* Path to the fixture JSON file to validate |

### Examples

**Validate a fixture file:**

```bash
python -m context_reliability_bench.validate_cli --fixture fixtures/sample.json
# OK: 3 case(s) validated
```

**Catch a malformed fixture (exits with code 1):**

```bash
python -m context_reliability_bench.validate_cli --fixture bad.json
# Error: ...
echo $?
# 1
```

Run this as a pre-commit hook or CI step before running the full benchmark.

---

## 3. Common CI patterns

### Gate on metric thresholds

The CLI itself does not gate on thresholds. Use the Python API in a wrapper script:

```python
# scripts/ci_bench.py
import sys
from pathlib import Path
from context_reliability_bench.loader import load_fixture
from context_reliability_bench.metrics.precision_at_k import PrecisionAtK
from context_reliability_bench.metrics.protocol import Metric
from context_reliability_bench.quality_gates import (
    QualityGate,
    gates_exit_code,
    run_quality_gates,
)
from context_reliability_bench.runner import run_benchmark

cases = load_fixture(Path("fixtures/v1/noise_resistance.json"))
metrics: list[Metric] = [PrecisionAtK(k=5)]
result = run_benchmark(cases, metrics, run_id="ci")

gates = [QualityGate("precision@5", min_mean=0.50)]
report = run_quality_gates(result, gates)
sys.exit(gates_exit_code(report))
```

### Validate before benchmarking

```bash
# validate first — fail fast on bad fixtures
python -m context_reliability_bench.validate_cli --fixture fixtures/v1/noise_resistance.json

# then run the full benchmark
python -m context_reliability_bench \
    --fixture fixtures/v1/noise_resistance.json \
    --run-id $CI_COMMIT_SHA \
    --json-out artifacts/bench.json
```

### Use YAML config with batch runner

```bash
python - <<'EOF'
from pathlib import Path
from context_reliability_bench.batch import run_batch
from context_reliability_bench.config import load_yaml_config

config = load_yaml_config(Path("bench.yaml"))
result = run_batch([config])
for mr in result.results[0].metric_results:
    print(f"{mr.metric_name}: {mr.mean:.4f}")
EOF
```

---

## 4. All available Python entry points

| Invocation | Purpose |
|-----------|---------|
| `python -m context_reliability_bench` | Run benchmark CLI |
| `python -m context_reliability_bench.validate_cli` | Validate fixture |
| `python examples/basic_benchmark.py` | End-to-end example |
| `python examples/retriever_benchmark.py` | Retriever comparison |
| `python examples/generate_reports.py` | Export all report formats |
| `python examples/leaderboard_example.py` | Build and export leaderboard |

---

## 5. Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (invalid fixture, file not found, validation failure) |

Quality gates (`gates_exit_code`) return `0` when all gates pass, `1` when any fails.
