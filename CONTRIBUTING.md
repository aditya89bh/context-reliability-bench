# Contributing to context-reliability-bench

Thank you for taking the time to contribute! This document explains how to set up
your development environment, what the conventions are, and how to submit a change.

---

## Development Setup

```bash
git clone <repo-url>
cd context-reliability-bench
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Verify the setup:

```bash
python -m pytest                 # all tests should pass
python -m ruff check .           # no linting errors
python -m mypy .                 # no type errors
```

---

## Project Layout

```
src/context_reliability_bench/   ← library source (all public API)
tests/                           ← pytest test suite
fixtures/                        ← benchmark fixture JSON files
examples/                        ← runnable example scripts
docs/                            ← documentation markdown
```

---

## Coding Standards

### Style

- Formatter / linter: **ruff** (`line-length = 88`, rules: `E F I UP B SIM`)
- Type checker: **mypy** (strict mode, `warn_return_any = true`)
- All source files start with `from __future__ import annotations`

### Dataclasses

- Use `@dataclass(frozen=True)` for all model types
- Use a named `_default_xxx()` factory function for `frozenset` fields to satisfy
  mypy strict mode (avoids `frozenset[Any]` inference)

### Protocols

- Use `typing.Protocol` with `@runtime_checkable` for all structural interfaces
- Concrete implementations do **not** need to inherit from the protocol class

### Tests

- One test file per source module, named `test_<module>.py`
- Tests must not hit the network or filesystem beyond `fixtures/`
- Use `pytest.approx` for all floating-point comparisons
- `frozen=True` mutation tests use a try/except with `dataclasses.FrozenInstanceError`

---

## Running the Test Suite

```bash
python -m pytest                         # full suite
python -m pytest tests/test_runner.py   # single file
python -m pytest -k "precision"         # filter by name
```

---

## Making a Change

1. **Open an issue** (bug, feature request, or documentation improvement)
2. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feat/my-improvement
   ```
3. **Make your changes** — one logical change per commit
4. **Run validations** before committing:
   ```bash
   python -m ruff check .
   python -m mypy .
   python -m pytest
   ```
5. **Write tests** for every new behaviour
6. **Update documentation** in `docs/` if you changed a public API
7. **Open a pull request** against `main`

---

## Adding a New Metric

1. Create `src/context_reliability_bench/metrics/<name>.py`
2. Implement the `Metric` protocol:
   ```python
   from __future__ import annotations
   from dataclasses import dataclass
   from context_reliability_bench.metrics.protocol import Metric
   from context_reliability_bench.models.retrieved_context import RetrievedContext

   @dataclass(frozen=True)
   class MyMetric:
       k: int = 5

       @property
       def name(self) -> str:
           return f"my_metric@{self.k}"

       def compute(
           self,
           context: tuple[RetrievedContext, ...],
           relevant_doc_ids: frozenset[str],
       ) -> float:
           ...  # return a score in [0, 1]
   ```
3. Export it from `src/context_reliability_bench/metrics/__init__.py`
4. Add tests in `tests/test_metrics.py`

---

## Adding a New Retriever Adapter

1. Create `src/context_reliability_bench/retrieval/<name>.py`
2. Implement the `RetrieverAdapter` protocol (`name`, `index`, `retrieve`)
3. Export from `src/context_reliability_bench/retrieval/__init__.py`
4. Add tests in `tests/test_retrieval.py`
5. Scores returned by `retrieve()` must be in `[0.0, 1.0]`

---

## Adding a New Fixture Dataset

1. Create `fixtures/v1/<category>.json` following the schema:
   ```json
   {
     "format_version": "1.0",
     "category": "<category>",
     "cases": [ ... ]
   }
   ```
2. Add an entry in `fixtures/manifest.json`
3. Validate: `python -m context_reliability_bench.validate_cli --fixture fixtures/v1/<category>.json`
4. Add a category class in `src/context_reliability_bench/categories/`
5. Register it in `suite.build_default_registry()`

---

## Commit Style

```
Add <what>                    ← new feature / file
Fix <what>                    ← bug fix
Update <what>                 ← change to existing feature
Refactor <what>               ← internal restructuring
```

Keep the first line under 72 characters. No period at the end.

---

## Questions?

Open a GitHub issue with the label `question`.
