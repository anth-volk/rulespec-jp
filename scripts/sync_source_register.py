from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "data/source-register.yaml"
CONTENT_ROOTS = (
    ROOT / "jp/statutes",
    ROOT / "jp/regulations",
    ROOT / "jp/policies",
)


def main() -> None:
    register = yaml.safe_load(REGISTER.read_text())
    provisions = {
        item["citation_path"]: item for item in register["proof_provisions"]
    }
    for content_root in CONTENT_ROOTS:
        for path in sorted(content_root.rglob("*.yaml")):
            if path.name.endswith(".test.yaml"):
                continue
            payload = yaml.safe_load(path.read_text())
            for rule in payload["rules"]:
                atoms = rule.get("metadata", {}).get("proof", {}).get("atoms", [])
                for atom in atoms:
                    source = atom["source"]
                    citation_path = source["corpus_citation_path"]
                    provision = provisions.setdefault(
                        citation_path,
                        {"citation_path": citation_path, "excerpts": []},
                    )
                    if source["excerpt"] not in provision["excerpts"]:
                        provision["excerpts"].append(source["excerpt"])

    for provision in provisions.values():
        provision["excerpts"] = sorted(provision["excerpts"])
    register["proof_provisions"] = [
        provisions[path] for path in sorted(provisions)
    ]
    REGISTER.write_text(
        yaml.safe_dump(
            register,
            allow_unicode=True,
            sort_keys=False,
            width=100_000,
        )
    )


if __name__ == "__main__":
    main()
