from __future__ import annotations

from pathlib import Path
from typing import Any

from context_reliability_bench.config.model import BenchmarkConfig, ConfigError


def load_yaml_config(path: Path) -> BenchmarkConfig:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Cannot read config file: {path}") from exc
    data = _parse_simple_yaml(text)
    return _config_from_dict(data, source=str(path))


def _config_from_dict(
    data: dict[str, Any],
    source: str = "",
) -> BenchmarkConfig:
    fixture_path = data.get("fixture_path")
    if not isinstance(fixture_path, str):
        raise ConfigError(f"'{source}': fixture_path must be a string")

    run_id_raw = data.get("run_id", "default")
    run_id = run_id_raw if isinstance(run_id_raw, str) else "default"

    k_raw = data.get("k", 5)
    if not isinstance(k_raw, int) or k_raw <= 0:
        raise ConfigError(f"'{source}': k must be a positive integer")
    k: int = k_raw

    names_raw = data.get("metric_names")
    if names_raw is None:
        metric_names: tuple[str, ...] = (
            "precision",
            "recall",
            "ndcg",
            "mrr",
            "top_k_accuracy",
        )
    elif isinstance(names_raw, list):
        metric_names = tuple(str(m) for m in names_raw)
    else:
        raise ConfigError(f"'{source}': metric_names must be a list")

    out_json = data.get("output_json")
    out_csv = data.get("output_csv")

    tags_raw = data.get("tags")
    tags: frozenset[str]
    if isinstance(tags_raw, list):
        tags = frozenset(str(t) for t in tags_raw)
    else:
        tags = frozenset()

    return BenchmarkConfig(
        fixture_path=fixture_path,
        run_id=run_id,
        k=k,
        metric_names=metric_names,
        output_json=str(out_json) if out_json is not None else None,
        output_csv=str(out_csv) if out_csv is not None else None,
        tags=tags,
    )


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse a minimal YAML subset: scalars and flat block-style lists."""
    result: dict[str, Any] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip()
        stripped = raw.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        if ":" not in stripped:
            i += 1
            continue

        colon = stripped.index(":")
        key = stripped[:colon].strip()
        value = stripped[colon + 1 :].strip()

        if "#" in value:
            value = value[: value.index("#")].strip()

        if not value or value.lower() in ("null", "~"):
            # Look ahead for block-style list items
            j = i + 1
            items: list[str] = []
            while j < len(lines):
                next_stripped = lines[j].strip()
                if not next_stripped or next_stripped.startswith("#"):
                    j += 1
                    continue
                if next_stripped.startswith("- "):
                    items.append(next_stripped[2:].strip())
                    j += 1
                else:
                    break
            if items:
                result[key] = items
                i = j
            else:
                result[key] = None
                i += 1
        elif value.lower() == "true":
            result[key] = True
            i += 1
        elif value.lower() == "false":
            result[key] = False
            i += 1
        else:
            try:
                result[key] = int(value)
            except ValueError:
                try:
                    result[key] = float(value)
                except ValueError:
                    result[key] = value
            i += 1

    return result
