# Architecture Diagram

## Component Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      context-reliability-bench                       │
├─────────────────┬───────────────────┬───────────────────────────────┤
│   DATA LAYER    │   RETRIEVAL LAYER │       EVALUATION LAYER        │
│                 │                   │                               │
│  fixtures/      │  RetrieverAdapter │  Metrics                      │
│  ├── sample.json│  ├── InMemory     │  ├── PrecisionAtK             │
│  ├── manifest   │  ├── BM25         │  ├── RecallAtK                │
│  └── v1/        │  └── Vector       │  ├── NdcgAtK                  │
│      ├── noise  │  (VectorBackend)  │  ├── ReciprocalRank           │
│      ├── contra │                   │  └── TopKAccuracy             │
│      ├── temp   │  run_retriever_   │                               │
│      └── distr  │  benchmark()      │  run_benchmark()              │
│                 │                   │       │                       │
│  Loader         │  RetrievalQuery   │       ▼                       │
│  load_fixture() │                   │   RunResult                   │
│  load_versioned │                   │   MetricResult                │
│  _fixture()     │                   │                               │
└────────┬────────┴─────────┬─────────┴──────────┬────────────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ANALYSIS LAYER                              │
│                                                                     │
│  Stats               Scoring              Comparison               │
│  compute_metric_     aggregate_score()    BenchmarkComparison      │
│  stats()             category_scores()   Engine.compare()          │
│  run_stats()         weighted_score()                              │
│                                          Regression                │
│  Trend Analysis      Run History         RegressionDetector        │
│  analyze_trends()    BenchmarkHistory    .detect()                 │
│  MetricTrend         BenchmarkRunRecord                            │
│                                                                     │
│  Quality Gates                                                      │
│  run_quality_gates() → QualityGateReport → gates_exit_code()       │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          REPORT LAYER                               │
│                                                                     │
│  export_html()         export_markdown()     export_json()          │
│  export_csv()          export_leaderboard_json/csv()                │
│  export_comparison_*() export_dashboard_json()                      │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CONFIGURATION LAYER                           │
│                                                                     │
│  BenchmarkConfig      ExecutionProfile      load_yaml_config()      │
│  run_batch()          QUICK / STANDARD /    BenchmarkDiscovery      │
│  BatchResult          THOROUGH              from_default_manifest() │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Fixture JSON
     │
     ▼
load_fixture() ──► list[BenchmarkCase]
                         │
              ┌──────────┼──────────────────┐
              │          │                  │
              ▼          ▼                  ▼
         Metrics    Retriever          Validator
              │          │                  │
              └──────────┴──────────────────┘
                         │
                         ▼
                   run_benchmark()
                         │
                         ▼
                     RunResult
                    /    |    \
                   /     |     \
          Reports  Stats  Analysis
                         |
                   QualityGateReport
                         |
                   exit_code (0/1)
```

## Module Dependency Map

```
models/          ← shared by everything; no dependencies on other modules
loader.py        ← models/
runner.py        ← models/, metrics/
metrics/         ← models/
categories/      ← models/
suite.py         ← categories/, metrics/, models/, runner.py
discovery.py     ← models/
retrieval/       ← models/, metrics/, runner.py
config/          ← (no internal deps)
batch.py         ← config/, loader.py, metrics/, runner.py, scoring.py
stats.py         ← models/
scoring.py       ← models/, suite.py
history.py       ← models/
comparison_engine.py ← models/, history.py
trend.py         ← history.py
regression.py    ← models/
quality_gates.py ← models/
reports/         ← models/, stats.py, scoring.py, suite.py
leaderboard_export.py ← models/
validate_cli.py  ← loader.py, validation.py
```
