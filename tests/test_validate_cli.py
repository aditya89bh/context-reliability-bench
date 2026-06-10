from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_reliability_bench.validate_cli import validate_main

_ROOT = Path(__file__).parent.parent
_SAMPLE = _ROOT / "fixtures" / "sample.json"
_NOISE = _ROOT / "fixtures" / "v1" / "noise_resistance.json"


def test_valid_fixture_exits_0() -> None:
    assert validate_main(["--fixture", str(_SAMPLE)]) == 0


def test_missing_fixture_exits_1() -> None:
    assert validate_main(["--fixture", "/no/such/fixture.json"]) == 1


def test_invalid_json_exits_1(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert validate_main(["--fixture", str(bad)]) == 1


def test_missing_required_field_exits_1(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps({"cases": [{"id": "x"}]}), encoding="utf-8"
    )
    assert validate_main(["--fixture", str(bad)]) == 1


def test_all_v1_fixtures_exit_0() -> None:
    for name in (
        "noise_resistance",
        "contradiction",
        "temporal_relevance",
        "distractor",
    ):
        path = _ROOT / "fixtures" / "v1" / f"{name}.json"
        code = validate_main(["--fixture", str(path)])
        assert code == 0, f"Expected 0 for {name}, got {code}"


def test_output_reports_case_count(capsys: pytest.CaptureFixture[str]) -> None:
    validate_main(["--fixture", str(_NOISE)])
    captured = capsys.readouterr()
    assert "3" in captured.out
