from __future__ import annotations

from pathlib import Path

import pytest

from context_reliability_bench.config.model import ConfigError
from context_reliability_bench.config.yaml_config import (
    _config_from_dict,
    _parse_simple_yaml,
    load_yaml_config,
)

# ─── _parse_simple_yaml ───────────────────────────────────────────────────────


def test_parse_string_value() -> None:
    data = _parse_simple_yaml("fixture_path: fixtures/sample.json")
    assert data["fixture_path"] == "fixtures/sample.json"


def test_parse_int_value() -> None:
    data = _parse_simple_yaml("k: 5")
    assert data["k"] == 5


def test_parse_bool_true() -> None:
    data = _parse_simple_yaml("enabled: true")
    assert data["enabled"] is True


def test_parse_bool_false() -> None:
    data = _parse_simple_yaml("enabled: false")
    assert data["enabled"] is False


def test_parse_null_value() -> None:
    data = _parse_simple_yaml("output_json: null")
    assert data["output_json"] is None


def test_parse_tilde_null() -> None:
    data = _parse_simple_yaml("output_json: ~")
    assert data["output_json"] is None


def test_parse_block_list() -> None:
    yaml = "metric_names:\n  - precision\n  - recall\n"
    data = _parse_simple_yaml(yaml)
    assert data["metric_names"] == ["precision", "recall"]


def test_parse_comment_ignored() -> None:
    yaml = "# this is a comment\nk: 3\n"
    data = _parse_simple_yaml(yaml)
    assert data["k"] == 3


def test_parse_inline_comment_stripped() -> None:
    data = _parse_simple_yaml("k: 5  # five")
    assert data["k"] == 5


def test_parse_empty_line_ignored() -> None:
    data = _parse_simple_yaml("k: 5\n\nrun_id: test\n")
    assert data["k"] == 5
    assert data["run_id"] == "test"


# ─── _config_from_dict ────────────────────────────────────────────────────────


def test_config_from_dict_minimal() -> None:
    cfg = _config_from_dict({"fixture_path": "f.json"})
    assert cfg.fixture_path == "f.json"
    assert cfg.k == 5


def test_config_from_dict_full() -> None:
    cfg = _config_from_dict(
        {
            "fixture_path": "f.json",
            "run_id": "my-run",
            "k": 10,
            "metric_names": ["precision", "recall"],
            "output_json": "out.json",
            "tags": ["nightly"],
        }
    )
    assert cfg.run_id == "my-run"
    assert cfg.k == 10
    assert cfg.metric_names == ("precision", "recall")
    assert cfg.output_json == "out.json"
    assert "nightly" in cfg.tags


def test_config_from_dict_missing_fixture_raises() -> None:
    with pytest.raises(ConfigError, match="fixture_path"):
        _config_from_dict({})


def test_config_from_dict_bad_k_raises() -> None:
    with pytest.raises(ConfigError, match="k must be a positive integer"):
        _config_from_dict({"fixture_path": "f.json", "k": -1})


def test_config_from_dict_bad_metric_names_raises() -> None:
    with pytest.raises(ConfigError, match="metric_names"):
        _config_from_dict({"fixture_path": "f.json", "metric_names": "precision"})


# ─── load_yaml_config ─────────────────────────────────────────────────────────


_SAMPLE_YAML = """\
fixture_path: fixtures/v1/noise_resistance.json
run_id: ci-run
k: 3
metric_names:
  - precision
  - recall
tags:
  - nightly
  - ci
"""


def test_load_yaml_config(tmp_path: Path) -> None:
    p = tmp_path / "bench.yaml"
    p.write_text(_SAMPLE_YAML, encoding="utf-8")
    cfg = load_yaml_config(p)
    assert cfg.fixture_path == "fixtures/v1/noise_resistance.json"
    assert cfg.run_id == "ci-run"
    assert cfg.k == 3
    assert cfg.metric_names == ("precision", "recall")
    assert "nightly" in cfg.tags
    assert "ci" in cfg.tags


def test_load_yaml_config_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Cannot read"):
        load_yaml_config(tmp_path / "nonexistent.yaml")


def test_load_yaml_config_missing_fixture_path_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("run_id: test\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="fixture_path"):
        load_yaml_config(p)
