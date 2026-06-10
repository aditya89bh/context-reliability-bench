from __future__ import annotations

from pathlib import Path

from context_reliability_bench.models.run_result import RunResult


def export_markdown(result: RunResult, path: Path) -> None:
    lines = _build_lines(result)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_lines(result: RunResult) -> list[str]:
    lines: list[str] = [
        f"# Benchmark Report: {_cell(result.run_id)}",
        "",
        "## Summary",
        "",
        "| Metric | Mean Score |",
        "| --- | --- |",
    ]
    for mr in result.metric_results:
        lines.append(f"| {_cell(mr.metric_name)} | {mr.mean:.4f} |")

    for mr in result.metric_results:
        lines += [
            "",
            f"## {_cell(mr.metric_name)}",
            "",
            "| Case ID | Score |",
            "| --- | --- |",
        ]
        for cid, score in mr.case_scores:
            lines.append(f"| {_cell(cid)} | {score:.4f} |")

    return lines


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
