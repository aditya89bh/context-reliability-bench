# Changelog

All notable changes to `context-reliability-bench` are recorded here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] — 2026-06-11

### Added

- Core models: `Document`, `Query`, `RetrievedContext`, `BenchmarkCase`
- Fixture loader and structural validator
- `Metric` protocol; `PrecisionAtK`, `RecallAtK`, `NdcgAtK`, `ReciprocalRank`,
  `TopKAccuracy` metrics
- `RunResult` / `MetricResult` with per-case scores
- `run_benchmark` — evaluate cases against a list of metrics
- Retrieval adapters: `InMemoryRetrieverAdapter`, `BM25RetrieverAdapter`,
  `VectorRetrieverAdapter` / `VectorBackend` protocol
- `run_retriever_benchmark` — evaluate a live retriever
- `BenchmarkConfig` model, YAML config loader, execution profiles
- `run_batch` — execute multiple configs
- `BenchmarkHistory`, `BenchmarkComparisonEngine`, trend analysis, regression
  detection, quality gates
- Report exporters: HTML, Markdown, JSON, CSV, dashboard, comparison, leaderboard
- Suite runner (`build_default_registry`, `run_suite`)
- CLI entry points: `python -m context_reliability_bench`,
  `python -m context_reliability_bench.validate_cli`
- Benchmark fixtures: `fixtures/sample.json`, `fixtures/v1/` category fixtures,
  `fixtures/v1/large_dataset.json` (500 cases)
- Deterministic seed support, reproducibility metadata, execution timing
- Parallel execution (`run_parallel`), result caching (`BenchmarkCache`)
- GitHub Actions CI workflow, pytest-cov coverage reporting (≥ 80 %)
- Documentation: `README.md`, `docs/`, `CONTRIBUTING.md`, `CHANGELOG.md`
- Examples: `examples/` (runnable, no external dependencies)

---

[Unreleased]: https://github.com/aditya89bh/context-reliability-bench/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/aditya89bh/context-reliability-bench/releases/tag/v0.1.0
