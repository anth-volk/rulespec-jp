from __future__ import annotations

import calendar
import json
import os
import shutil
import subprocess
from decimal import Decimal
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


def _compose_and_compile(
    compose: Path, engine: Path, program: Path, tmp_path: Path
) -> tuple[dict, Path]:
    composed = tmp_path / f"{program.stem}.rulespec.yaml"
    artifact = tmp_path / f"{program.stem}.compiled.json"
    composition = subprocess.run(
        (
            str(compose),
            str(program),
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
    return yaml.safe_load(composed.read_text()), artifact


def _compile_module(engine: Path, relative: str, tmp_path: Path) -> Path:
    module = ROOT / relative
    artifact = tmp_path / f"{module.stem}-{abs(hash(relative))}.compiled.json"
    compilation = subprocess.run(
        (
            str(engine),
            "compile",
            "--program",
            str(module),
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
    return artifact


def _execute(
    engine: Path,
    artifact: Path,
    period: dict,
    inputs: dict,
    outputs: list[str],
) -> dict[str, Decimal]:
    encoded_inputs = []
    for name, value in inputs.items():
        scalar = (
            {"kind": "bool", "value": value}
            if isinstance(value, bool)
            else {"kind": "decimal", "value": str(value)}
        )
        encoded_inputs.append(
            {
                "name": name,
                "entity": "Person",
                "entity_id": "person:1",
                "interval": {"start": period["start"], "end": period["end"]},
                "value": scalar,
            }
        )
    execution = subprocess.run(
        (str(engine), "run-compiled", "--artifact", str(artifact)),
        input=json.dumps(
            {
                "mode": "fast",
                "dataset": {"inputs": encoded_inputs, "relations": []},
                "queries": [
                    {
                        "entity_id": "person:1",
                        "period": period,
                        "outputs": outputs,
                    }
                ],
            }
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert execution.returncode == 0, execution.stderr
    values = json.loads(execution.stdout)["results"][0]["outputs"]
    return {
        output: Decimal(values[output]["value"]["value"])
        for output in outputs
    }


def test_legacy_start_boundary_program_still_composes(tmp_path):
    compose = _required_binary("AXIOM_COMPOSE_BIN")
    engine = _required_binary("AXIOM_RULES_ENGINE_BIN")
    payload, artifact = _compose_and_compile(
        compose,
        engine,
        ROOT / "jp/programs/national-income-tax-2017.yaml",
        tmp_path,
    )
    assert payload["module"]["kind"] == "composition"
    assert artifact.is_file()
    assert {
        "jp:statutes/e-gov/340ac0000000033/article/28",
        "jp:statutes/e-gov/340ac0000000033/article/22",
        "jp:statutes/e-gov/337ac0000000066/article/118",
        "jp:statutes/e-gov/423ac0000000117/article/13",
    }.issubset(set(payload["imports"]))


def test_wave1_2018_complete_annual_component_ledger(tmp_path):
    compose = _required_binary("AXIOM_COMPOSE_BIN")
    engine = _required_binary("AXIOM_RULES_ENGINE_BIN")
    scenario = yaml.safe_load(
        (ROOT / "data/scenarios/wave1-2018-working-parent.yaml").read_text()
    )
    assert "not disposable income" in scenario["scope_note"]

    _, tax_artifact = _compose_and_compile(
        compose,
        engine,
        ROOT / "jp/programs/national-income-tax-wave1.yaml",
        tmp_path,
    )
    pension_artifact = _compile_module(
        engine,
        "jp/statutes/e-gov/329ac0000000115/article/81.yaml",
        tmp_path,
    )
    employment_insurance_artifact = _compile_module(
        engine,
        "jp/policies/mhlw/employment-insurance/fy2017-rates.yaml",
        tmp_path,
    )
    child_allowance_artifact = _compile_module(
        engine,
        "jp/statutes/e-gov/346ac0000000073/article/6.yaml",
        tmp_path,
    )

    pension_output = (
        "jp:statutes/e-gov/329ac0000000115/article/81"
        "#japan_employees_pension_employee_total_contribution"
    )
    employment_insurance_output = (
        "jp:policies/mhlw/employment-insurance/fy2017-rates"
        "#japan_employment_insurance_employee_contribution"
    )
    child_allowance_output = (
        "jp:statutes/e-gov/346ac0000000073/article/6"
        "#japan_child_allowance_monthly"
    )
    annual_pension = Decimal(0)
    annual_employment_insurance = Decimal(0)
    annual_child_allowance = Decimal(0)
    for month in range(1, 13):
        last_day = calendar.monthrange(2018, month)[1]
        month_period = {
            "period_kind": "month",
            "start": f"2018-{month:02d}-01",
            "end": f"2018-{month:02d}-{last_day:02d}",
        }
        annual_pension += _execute(
            engine,
            pension_artifact,
            month_period,
            scenario["monthly_employees_pension_inputs"],
            [pension_output],
        )[pension_output]
        annual_employment_insurance += _execute(
            engine,
            employment_insurance_artifact,
            month_period,
            scenario["monthly_employment_insurance_inputs"],
            [employment_insurance_output],
        )[employment_insurance_output]
        annual_child_allowance += _execute(
            engine,
            child_allowance_artifact,
            month_period,
            scenario["monthly_child_allowance_inputs"],
            [child_allowance_output],
        )[child_allowance_output]

    expected = {
        name: Decimal(str(value))
        for name, value in scenario["expected_components"].items()
    }
    assert annual_pension == expected["employees_pension_employee_contribution"]
    assert (
        annual_employment_insurance
        == expected["employment_insurance_employee_contribution"]
    )
    assert (
        annual_pension + annual_employment_insurance
        == expected["nationally_uniform_employee_contributions"]
    )
    assert annual_child_allowance == expected["child_allowance"]

    tax_outputs = {
        "employment_income": (
            "jp:statutes/e-gov/340ac0000000033/article/28"
            "#japan_employment_income_article_28"
        ),
        "taxable_general_income": (
            "jp:statutes/e-gov/337ac0000000066/article/118"
            "#japan_pit_taxable_general_income"
        ),
        "base_national_income_tax": (
            "jp:statutes/e-gov/340ac0000000033/article/89"
            "#japan_national_income_tax_article_89_base_tax"
        ),
        "reconstruction_special_income_tax": (
            "jp:statutes/e-gov/423ac0000000117/article/13"
            "#japan_reconstruction_special_income_tax"
        ),
        "national_income_tax_including_surtax": (
            "jp:policies/nta/defense-special-income-tax/2027"
            "#japan_national_income_tax_including_national_surtaxes"
        ),
    }
    tax = _execute(
        engine,
        tax_artifact,
        scenario["period"],
        scenario["annual_tax_inputs"],
        list(tax_outputs.values()),
    )
    for expected_name, output in tax_outputs.items():
        assert tax[output] == expected[expected_name]
