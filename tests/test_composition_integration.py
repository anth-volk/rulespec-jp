from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _required_binary(environment_name: str) -> Path:
    raw = os.environ.get(environment_name)
    if not raw:
        pytest.skip(f"{environment_name} is required for composition integration")
    discovered = shutil.which(raw)
    binary = Path(discovered or raw).expanduser().resolve()
    assert binary.is_file(), f"missing executable: {binary}"
    return binary


def test_national_income_tax_program_composes_and_compiles(tmp_path):
    compose = _required_binary("AXIOM_COMPOSE_BIN")
    engine = _required_binary("AXIOM_RULES_ENGINE_BIN")
    composed = tmp_path / "national-income-tax.rulespec.yaml"
    artifact = tmp_path / "national-income-tax.compiled.json"

    composition = subprocess.run(
        (
            str(compose),
            str(ROOT / "jp/programs/national-income-tax-2017.yaml"),
            "--rulespec-root",
            str(ROOT),
            "--output",
            str(composed),
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert composition.returncode == 0, composition.stderr
    payload = yaml.safe_load(composed.read_text())
    assert payload["module"]["kind"] == "composition"
    assert payload["imports"] == [
        "jp:statutes/e-gov/340ac0000000033/article/28",
        "jp:statutes/e-gov/340ac0000000033/article/89",
        "jp:statutes/e-gov/423ac0000000117/article/13",
    ]

    compilation = subprocess.run(
        (
            str(engine),
            "compile-composed",
            "--program",
            str(composed),
            "--rulespec-root",
            str(ROOT),
            "--output",
            str(artifact),
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert compilation.returncode == 0, compilation.stderr
    assert artifact.is_file()
