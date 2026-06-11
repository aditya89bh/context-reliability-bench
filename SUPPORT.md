# Support

## Where to get help

| Channel | Use for |
|---------|---------|
| [GitHub Issues](https://github.com/aditya89bh/context-reliability-bench/issues) | Bug reports, feature requests, documentation gaps |
| [GitHub Discussions](https://github.com/aditya89bh/context-reliability-bench/discussions) | Usage questions, ideas, general discussion |

## Before opening an issue

1. **Search existing issues** — your question may already be answered.
2. **Check the documentation** — start with [`docs/index.md`](docs/index.md)
   and the [quickstart guide](docs/quickstart.md).
3. **Run the validation suite** to confirm the library is installed correctly:
   ```bash
   python -m pytest
   python -m context_reliability_bench.validate_cli --fixture fixtures/sample.json
   ```

## Reporting a bug

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:

- Python version (`python --version`)
- Library version (`python -c "import context_reliability_bench; print(context_reliability_bench.__version__)"`)
- Minimal reproducible example
- Full traceback

## Requesting a feature

Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).
Describe the problem you are trying to solve rather than the specific
implementation you have in mind.

## Security vulnerabilities

Do **not** open a public issue.  See [`SECURITY.md`](SECURITY.md) for the
responsible disclosure process.

## Response time

This is a personal open-source project maintained on a best-effort basis.
Issues are reviewed when time permits.  There is no guaranteed response SLA.
