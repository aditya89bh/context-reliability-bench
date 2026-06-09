from __future__ import annotations

import json
from pathlib import Path

from context_reliability_bench.__main__ import main

SAMPLE_FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample.json"


def test_cli_success_exit_code() -> None:
    code = main(["--fixture", str(SAMPLE_FIXTURE)])
    assert code == 0


def test_cli_missing_fixture_exit_code() -> None:
    code = main(["--fixture", "/no/such/fixture.json"])
    assert code == 1


def test_cli_json_output(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    code = main(["--fixture", str(SAMPLE_FIXTURE), "--json-out", str(out)])
    assert code == 0
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "run_id" in data
    assert "metrics" in data


def test_cli_csv_output(tmp_path: Path) -> None:
    out = tmp_path / "report.csv"
    code = main(["--fixture", str(SAMPLE_FIXTURE), "--csv-out", str(out)])
    assert code == 0
    assert out.exists()
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "run_id,metric,case_id,score"


def test_cli_custom_run_id(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    code = main(
        ["--fixture", str(SAMPLE_FIXTURE), "--run-id", "ci-run", "--json-out", str(out)]
    )
    assert code == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["run_id"] == "ci-run"


def test_cli_custom_k(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    code = main(
        ["--fixture", str(SAMPLE_FIXTURE), "--k", "1", "--json-out", str(out)]
    )
    assert code == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "precision@1" in data["metrics"]
