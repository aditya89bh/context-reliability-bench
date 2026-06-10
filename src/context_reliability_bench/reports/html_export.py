from __future__ import annotations

import html as _html
from pathlib import Path

from context_reliability_bench.models.run_result import RunResult

_CSS = (
    "body{font-family:system-ui,sans-serif;max-width:960px;"
    "margin:2rem auto;padding:0 1rem;color:#222}"
    "h1{border-bottom:2px solid #333;padding-bottom:.5rem}"
    "h2{margin-top:2rem}"
    "table{border-collapse:collapse;width:100%;margin-top:1rem}"
    "th,td{border:1px solid #ccc;padding:8px 12px;text-align:left}"
    "th{background:#f5f5f5;font-weight:600}"
    "tr:nth-child(even){background:#fafafa}"
    ".score{font-variant-numeric:tabular-nums}"
)


def export_html(result: RunResult, path: Path) -> None:
    title = f"Benchmark Report: {_esc(result.run_id)}"
    body = _build_body(result)
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{title}</title>",
        f"<style>{_CSS}</style>",
        "</head>",
        "<body>",
        body,
        "</body>",
        "</html>",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _build_body(result: RunResult) -> str:
    rid = _esc(result.run_id)
    parts: list[str] = [
        "<h1>Benchmark Report</h1>",
        f"<p><strong>Run ID:</strong> {rid}</p>",
        "<h2>Summary</h2>",
        "<table>",
        "<thead><tr><th>Metric</th><th>Mean Score</th></tr></thead>",
        "<tbody>",
    ]
    for mr in result.metric_results:
        parts.append(
            f"<tr><td>{_esc(mr.metric_name)}</td>"
            f"<td class='score'>{mr.mean:.4f}</td></tr>"
        )
    parts.append("</tbody></table>")

    for mr in result.metric_results:
        parts.append(f"<h2>{_esc(mr.metric_name)}</h2>")
        parts += [
            "<table>",
            "<thead><tr><th>Case ID</th><th>Score</th></tr></thead>",
            "<tbody>",
        ]
        for cid, score in mr.case_scores:
            parts.append(
                f"<tr><td>{_esc(cid)}</td>"
                f"<td class='score'>{score:.4f}</td></tr>"
            )
        parts.append("</tbody></table>")

    return "\n".join(parts)


def _esc(s: str) -> str:
    return _html.escape(s)
