from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOTS = tuple(ROOT.glob("jp/statutes")) + tuple(ROOT.glob("jp/regulations")) + tuple(
    ROOT.glob("jp/policies")
)


def _rulespec_files() -> list[Path]:
    return sorted(
        path
        for root in CONTENT_ROOTS
        for path in root.rglob("*.yaml")
        if not path.name.endswith(".test.yaml")
    )


def test_only_japan_namespace_is_present():
    jurisdictions = {
        path.name
        for path in ROOT.iterdir()
        if path.is_dir() and re.fullmatch(r"[a-z]{2}(?:-[a-z0-9-]+)*", path.name)
    }
    assert jurisdictions == {"jp"}


def test_every_rulespec_has_companion_test():
    for path in _rulespec_files():
        companion = path.with_name(path.stem + ".test.yaml")
        assert companion.exists(), f"{path.relative_to(ROOT)} lacks {companion.name}"


def test_every_rulespec_uses_v1_and_jpy_zero_minor_units():
    for path in _rulespec_files():
        payload = yaml.safe_load(path.read_text())
        assert payload["format"] == "rulespec/v1"
        jpy = [unit for unit in payload.get("units", []) if unit.get("name") == "JPY"]
        assert jpy and jpy[0]["minor_units"] == 0


def test_money_atom_ratchet_is_zero():
    payload = yaml.safe_load((ROOT / "known-missing-money-atoms.yaml").read_text())
    assert payload == {"total_allowed": 0}


def test_oracle_pending_ceiling_matches_explicit_entries():
    payload = yaml.safe_load((ROOT / "oracle-coverage-pending.yaml").read_text())
    assert payload["ceiling"] == len(payload["entries"])


def test_source_and_oracle_ledgers_are_japan_scoped():
    coverage = json.loads((ROOT / "data/coverage/tax-benefit-source-map.json").read_text())
    oracle = json.loads((ROOT / "data/oracles/oracle-index.json").read_text())
    assert coverage["jurisdiction"] == oracle["jurisdiction"] == "jp"
    assert coverage["inclusive_start"] == "2017-04-01"


def test_validation_status_does_not_claim_canonical_apply_or_oracle_completion():
    payload = json.loads((ROOT / "data/validation/implementation-status.json").read_text())
    assert payload["canonical_axiom_apply"] is False
    assert payload["checks"]["protected_proof_validate"]["status"] == "blocked-as-designed"
    assert payload["checks"]["independent_oracle"]["status"] == "pending"


def test_proof_excerpts_exist_in_source_register():
    register = yaml.safe_load((ROOT / "data/source-register.yaml").read_text())
    excerpts_by_path = {
        item["citation_path"]: set(item["excerpts"])
        for item in register["proof_provisions"]
    }
    for path in _rulespec_files():
        payload = yaml.safe_load(path.read_text())
        for rule in payload["rules"]:
            atoms = rule.get("metadata", {}).get("proof", {}).get("atoms", [])
            for atom in atoms:
                source = atom["source"]
                assert source["excerpt"] in excerpts_by_path[source["corpus_citation_path"]]


def test_pre_start_month_is_never_claimed():
    for path in _rulespec_files():
        payload = yaml.safe_load(path.read_text())
        for rule in payload["rules"]:
            for version in rule.get("versions", []):
                assert version["effective_from"] >= "2017-04-01"
