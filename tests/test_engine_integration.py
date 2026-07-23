from __future__ import annotations

import json
import os
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ENV = "AXIOM_RULES_ENGINE_BIN"
RULESPEC_MODULES = sorted(
    str(path.relative_to(ROOT))
    for content_root in (
        ROOT / "jp/statutes",
        ROOT / "jp/regulations",
        ROOT / "jp/policies",
    )
    if content_root.exists()
    for path in content_root.rglob("*.yaml")
    if not path.name.endswith(".test.yaml")
)


def _engine() -> Path:
    raw = os.environ.get(ENGINE_ENV)
    if not raw:
        pytest.skip(f"{ENGINE_ENV} is required for executable RuleSpec cases")
    engine = Path(raw).expanduser().resolve()
    assert engine.is_file(), f"rules engine does not exist: {engine}"
    return engine


def _run(engine: Path, *args: str, input_payload: dict | None = None) -> dict:
    completed = subprocess.run(
        (str(engine), *args),
        cwd=ROOT,
        input=None if input_payload is None else json.dumps(input_payload),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    if input_payload is None:
        return {}
    return json.loads(completed.stdout)


@pytest.mark.parametrize(
    "relative_module",
    RULESPEC_MODULES,
)
def test_companion_cases_execute_with_forked_engine(tmp_path, relative_module):
    engine = _engine()
    module_path = ROOT / relative_module
    artifact = tmp_path / f"{module_path.stem}.compiled.json"
    _run(
        engine,
        "compile",
        "--program",
        str(module_path),
        "--rulespec-root",
        str(ROOT),
        "--output",
        str(artifact),
    )

    cases = yaml.safe_load(module_path.with_name(f"{module_path.stem}.test.yaml").read_text())
    for case in cases:
        period = case["period"]
        inputs = []
        for name, value in case.get("input", {}).items():
            scalar = (
                {"kind": "bool", "value": value}
                if isinstance(value, bool)
                else {"kind": "decimal", "value": str(value)}
            )
            inputs.append(
                {
                    "name": name,
                    "entity": "Person",
                    "entity_id": "person:1",
                    "interval": {"start": period["start"], "end": period["end"]},
                    "value": scalar,
                }
            )
        response = _run(
            engine,
            "run-compiled",
            "--artifact",
            str(artifact),
            input_payload={
                "mode": "fast",
                "dataset": {"inputs": inputs, "relations": []},
                "queries": [
                    {
                        "entity_id": "person:1",
                        "period": period,
                        "outputs": list(case["output"]),
                    }
                ],
            },
        )
        actual_outputs = response["results"][0]["outputs"]
        for output_id, expected in case["output"].items():
            actual = actual_outputs[output_id]["value"]["value"]
            assert Decimal(actual) == Decimal(str(expected)), case["name"]


def test_toolchain_pins_exact_experimental_manifest_and_waiver_bytes():
    import hashlib
    import tomllib

    toolchain = tomllib.loads((ROOT / ".axiom/toolchain.toml").read_text())["toolchain"]
    assert toolchain["axiom_corpus_release"] == "jp-wave1-2017-04-01-v0-5-0"
    assert toolchain["axiom_corpus_release_content_sha256"] == (
        "e610136398036d538b7e8cbd521c2dc1f5034ee4b34a613345438209c3bd1af3"
    )
    waiver = (ROOT / "known-validation-gaps.yaml").read_bytes()
    assert hashlib.sha256(waiver).hexdigest() == toolchain["validation_waiver_set_sha256"]
