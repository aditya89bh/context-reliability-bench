# Changelog

All notable changes to `context-reliability-bench` are recorded here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- `docs/index.md` — documentation hub and navigation index

---

## [0.4.0] — Documentation and Examples

### Added

- `CONTRIBUTING.md` — development setup, coding standards, extension guides
- `CHANGELOG.md` — this file
- `docs/cli_walkthrough.md` — CLI flags, examples, and CI integration patterns
- `docs/tutorial.md` — 8-part tutorial: fixture → retriever → reports → CI → trends
- `docs/quickstart.md` — 6-step getting-started guide
- `docs/benchmark_lifecycle.md` — full lifecycle from case definition to CI gate
- `docs/assets/architecture.md` — ASCII architecture diagrams: component overview,
  data flow, module dependency map
- `examples/basic_benchmark.py` — end-to-end benchmark with fixture, metrics, gates
- `examples/retriever_benchmark.py` — BM25 vs InMemory comparison with regression check
- `examples/langchain_integration.py` — `VectorBackend` adapter for LangChain
- `examples/llamaindex_integration.py` — `RetrieverAdapter` bridge for LlamaIndex
- `examples/generate_reports.py` — HTML/Markdown/JSON/CSV/dashboard exports
- `examples/leaderboard_example.py` — multi-system leaderboard with JSON/CSV export
- README expanded as the primary entry point with API overview, examples, and doc links

### Changed

- `pyproject.toml`: added `exclude = ["examples/"]` to mypy config so examples are
  not subject to strict type checking

---

## [0.3.0] — Retrieval Layer and Quality Gates

### Added

- `RetrieverAdapter` protocol — pluggable retrieval interface
- `InMemoryRetrieverAdapter` — term-overlap retriever (no external deps)
- `BM25RetrieverAdapter` — BM25 retriever with k1=1.5, b=0.75
- `VectorRetrieverAdapter` + `VectorBackend` protocol — adapter for any vector store
- `RetrievalQuery` model — links query text to ground-truth relevant document IDs
- `run_retriever_benchmark` — evaluate a live retriever instead of pre-computed context
- `BenchmarkConfig` model — structured run configuration
- `load_yaml_config` — pure-Python YAML config loader (no PyYAML dependency)
- `ExecutionProfile` enum — QUICK / STANDARD / THOROUGH preset configurations
- `run_batch` — execute multiple `BenchmarkConfig` runs in one call
- `BenchmarkHistory` + `BenchmarkRunRecord` — store and query run history
- `BenchmarkComparisonEngine` — baseline vs candidate metric comparison
- `analyze_trends` — linear trend analysis (slope, direction) over history
- `RegressionDetector` — per-metric regression detection with absolute/relative thresholds
- `QualityGate` + `run_quality_gates` + `gates_exit_code` — CI-compatible pass/fail checks

---

## [0.2.0] — Metrics, Reports, and Suite Infrastructure

### Added

- `NdcgAtK` — Normalized Discounted Cumulative Gain
- `ReciprocalRank` — Mean Reciprocal Rank
- `TopKAccuracy` — whether any relevant document appears in top K
- `WeightedScoringMixin` — per-case weight support for all metrics
- `MetricRegistry` — discover and look up metrics by name
- `BenchmarkSuite` + `SuiteResult` — run multiple categories and aggregate
- `build_default_registry` — pre-populated suite with built-in categories
- `VersionedDatasetAdapter` — loads any fixture version
- `DatasetManifest` — machine-readable registry of all available fixtures
- HTML, Markdown, JSON, CSV report exporters
- Comparison report exporters (JSON + Markdown)
- Dashboard JSON exporter
- Leaderboard model (`Leaderboard`, `LeaderboardEntry`) with `ranked_by`
- `export_leaderboard_json` / `export_leaderboard_csv`
- Descriptive statistics module (`mean`, `std_dev`, `median`, `percentile`)
- Scoring utilities (`scale_score`, `clamp_score`, `aggregate_scores`)
- CLI entry point (`python -m context_reliability_bench`)
- Fixture validator CLI (`python -m context_reliability_bench.validate_cli`)

### Changed

- `MetricResult` records per-case scores as `tuple[tuple[str, float], ...]`

---

## [0.1.0] — Core Models and Evaluation Engine

### Added

- `Document` model — `id`, `content`, `metadata`
- `Query` model — `id`, `text`
- `RetrievedContext` model — `document`, `score`, `rank`
- `BenchmarkCase` model — links query, retrieved context, and ground truth
- Fixture loader — parse benchmark cases from JSON
- Fixture validator — structural validation with descriptive error messages
- `Metric` protocol — `name` property + `compute(context, relevant_doc_ids) -> float`
- `PrecisionAtK` metric
- `RecallAtK` metric
- `RunResult` + `MetricResult` — structured results with `mean`, `std_dev`, `min`, `max`
- `run_benchmark` — evaluate a sequence of cases against a list of metrics
- Initial benchmark fixture: `fixtures/sample.json` (3 cases)
- Versioned fixtures: `fixtures/v1/` with `noise_resistance`, `multi_hop`, `long_context`,
  `cross_lingual`, `temporal_reasoning` categories
- Full pytest test suite (`tests/`)
- mypy strict mode, ruff linting, pytest configuration

---

[Unreleased]: https://github.com/example/context-reliability-bench/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/example/context-reliability-bench/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/example/context-reliability-bench/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/example/context-reliability-bench/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/example/context-reliability-bench/releases/tag/v0.1.0
