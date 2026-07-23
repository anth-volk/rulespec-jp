#!/usr/bin/env python3
"""Validate every RuleSpec proof excerpt against retained Japan corpus rows."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

CITATION_PATTERN = re.compile(br'"citation_path":\s*"([^"]+)"')


def _proof_requirements(root: Path) -> dict[str, set[str]]:
    requirements: dict[str, set[str]] = defaultdict(set)
    for content_root in ("statutes", "regulations", "policies"):
        for path in sorted((root / "jp" / content_root).rglob("*.yaml")):
            if path.name.endswith(".test.yaml"):
                continue
            payload = yaml.safe_load(path.read_text())
            for rule in payload.get("rules", []):
                atoms = rule.get("metadata", {}).get("proof", {}).get("atoms", [])
                for atom in atoms:
                    source = atom["source"]
                    requirements[source["corpus_citation_path"]].add(source["excerpt"])
    return dict(requirements)


def _default_provision_files(corpus_data: Path) -> tuple[Path, ...]:
    relative_paths = (
        "provisions/jp/statute/2017-04-01-jp-wave1-full.jsonl",
        "provisions/jp/regulation/2017-04-01-jp-wave1-regulations.jsonl",
        "provisions/jp/guidance/2017-04-01-jp-wave1-agency-guidance.jsonl",
    )
    return tuple(corpus_data / relative for relative in relative_paths)


def validate(
    root: Path,
    provision_files: tuple[Path, ...],
) -> dict[str, object]:
    requirements = _proof_requirements(root)
    unresolved = set(requirements)
    missing_excerpts: dict[str, list[str]] = {}
    matched_excerpts = 0

    for path in provision_files:
        if not path.is_file():
            raise FileNotFoundError(f"missing corpus provision artifact: {path}")
        with path.open("rb") as stream:
            for line in stream:
                match = CITATION_PATTERN.search(line)
                if match is None:
                    continue
                citation_path = match.group(1).decode()
                if citation_path not in unresolved:
                    continue
                record = json.loads(line)
                body = record.get("body") or ""
                missing = sorted(
                    excerpt
                    for excerpt in requirements[citation_path]
                    if excerpt not in body
                )
                if missing:
                    missing_excerpts[citation_path] = missing
                else:
                    matched_excerpts += len(requirements[citation_path])
                unresolved.remove(citation_path)

    return {
        "passed": not unresolved and not missing_excerpts,
        "citation_paths_required": len(requirements),
        "citation_paths_matched": len(requirements) - len(unresolved),
        "proof_excerpts_required": sum(map(len, requirements.values())),
        "proof_excerpts_matched": matched_excerpts,
        "missing_citation_paths": sorted(unresolved),
        "missing_excerpts": missing_excerpts,
        "provision_files": [str(path) for path in provision_files],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="rulespec-jp checkout",
    )
    parser.add_argument(
        "--corpus-data",
        type=Path,
        required=True,
        help="axiom-corpus data/corpus directory",
    )
    parser.add_argument(
        "--provisions",
        action="append",
        type=Path,
        help="explicit provision JSONL; repeat to override the Wave 1 defaults",
    )
    args = parser.parse_args()
    provision_files = (
        tuple(args.provisions)
        if args.provisions
        else _default_provision_files(args.corpus_data)
    )
    result = validate(args.root.resolve(), provision_files)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
