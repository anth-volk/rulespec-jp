from __future__ import annotations

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
        "jp:statutes/e-gov/332ac0000000026/article/41-15-3",
        "jp:statutes/e-gov/340ac0000000033/article/35",
        "jp:statutes/e-gov/340ac0000000033/article/22",
        "jp:statutes/e-gov/340ac0000000033/article/74",
        "jp:statutes/e-gov/340ac0000000033/article/86",
        "jp:statutes/e-gov/337ac0000000066/article/118",
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

    period = {
        "period_kind": "custom",
        "name": "supported_start_date_assessment_window",
        "start": "2017-04-01",
        "end": "2018-01-01",
    }
    taxable_output = (
        "jp:statutes/e-gov/337ac0000000066/article/118"
        "#japan_pit_taxable_general_income"
    )
    base_tax_output = (
        "jp:statutes/e-gov/340ac0000000033/article/89"
        "#japan_national_income_tax_article_89_base_tax"
    )
    combined_tax_output = (
        "jp:statutes/e-gov/423ac0000000117/article/13"
        "#japan_national_income_tax_including_reconstruction_tax"
    )
    execution = subprocess.run(
        (str(engine), "run-compiled", "--artifact", str(artifact)),
        input=json.dumps(
            {
                "mode": "fast",
                "dataset": {
                    "inputs": [
                        {
                            "name": (
                                "jp:statutes/e-gov/340ac0000000033/article/28"
                                "#input.japan_employment_gross_cash_earnings"
                            ),
                            "entity": "Person",
                            "entity_id": "person:1",
                            "interval": {"start": period["start"], "end": period["end"]},
                            "value": {"kind": "decimal", "value": "5000000"},
                        },
                        {
                            "name": (
                                "jp:statutes/e-gov/332ac0000000026/article/41-15-3"
                                "#input.japan_public_pension_gross_receipts"
                            ),
                            "entity": "Person",
                            "entity_id": "person:1",
                            "interval": {"start": period["start"], "end": period["end"]},
                            "value": {"kind": "decimal", "value": "3500000"},
                        },
                        {
                            "name": (
                                "jp:statutes/e-gov/332ac0000000026/article/41-15-3"
                                "#input.japan_public_pension_recipient_age_at_statutory_test_date"
                            ),
                            "entity": "Person",
                            "entity_id": "person:1",
                            "interval": {"start": period["start"], "end": period["end"]},
                            "value": {"kind": "decimal", "value": "65"},
                        },
                        {
                            "name": (
                                "jp:statutes/e-gov/340ac0000000033/article/74"
                                "#input.japan_social_insurance_contributions_paid_or_withheld"
                            ),
                            "entity": "Person",
                            "entity_id": "person:1",
                            "interval": {"start": period["start"], "end": period["end"]},
                            "value": {"kind": "decimal", "value": "450123"},
                        },
                    ],
                    "relations": [],
                },
                "queries": [
                    {
                        "entity_id": "person:1",
                        "period": period,
                        "outputs": [
                            taxable_output,
                            base_tax_output,
                            combined_tax_output,
                        ],
                    }
                ],
            }
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert execution.returncode == 0, execution.stderr
    outputs = json.loads(execution.stdout)["results"][0]["outputs"]
    assert Decimal(outputs[taxable_output]["value"]["value"]) == Decimal("4879000")
    assert Decimal(outputs[base_tax_output]["value"]["value"]) == Decimal("548300")
    assert Decimal(outputs[combined_tax_output]["value"]["value"]) == Decimal("559814")
