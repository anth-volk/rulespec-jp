# rulespec-jp

Independent, public Axiom-compatible encodings of Japanese national tax and
benefit law, with an inclusive support boundary of **2017-04-01**.

This repository is maintained under `anth-volk`. It is not an official Axiom
Foundation jurisdiction, is not listed in an Axiom lane registry, and does not
send issues, branches, pull requests, releases, or signing material upstream.

## Current release state

The repository is an experimental `v0.x` implementation. The first executable
vertical slice covers:

- Income Tax Act article 89: the national progressive rate schedule; and
- Reconstruction Funding Special Measures Act article 13: the 2.1% special
  reconstruction income tax;
- the Japan Pension Service's five National Pension contribution amounts for
  平成29年度; and
- the three MHLW employee Employment Insurance rates for 平成29年度.

The pension and employment-insurance modules are parameter slices, not complete
contribution calculators. The complete Wave 1 source inventory is present, but
all remaining surfaces are explicitly statused in the coverage ledger.

## Time and calendar contract

- Monthly benefits and contributions begin in April 2017. March 2017 and
  earlier months are unsupported.
- Tax Year 2017 may be evaluated as an annual liability only where the April 1
  consolidated law and NTA annual material establish the applicable rule.
- Gregorian ISO dates control ordering and execution.
- Japanese era expressions are retained verbatim in provenance. For example,
  `平成29年4月1日` normalizes to `2017-04-01`, and `平成29年度` normalizes to
  `2017-04-01/2018-03-31`.

## Repository contract

- `jp/statutes`, `jp/regulations`, and `jp/policies` contain atomic RuleSpec.
- `jp/programs` contains declarative composition requests only.
- Every atomic module has a companion `.test.yaml`.
- JPY uses zero minor units.
- Original Japanese text is authoritative; English text is explanatory.
- No combined disposable-income output is published while inhabitant tax and
  non-uniform health and long-term-care premiums are out of scope.

## Validation

Run the fork-only checks from this repository after building the forked engine:

```bash
cargo build --manifest-path ../axiom-rules-engine/Cargo.toml --locked
AXIOM_RULES_ENGINE_BIN=../axiom-rules-engine/target/debug/axiom-rules-engine \
  python3 -m pytest -q
```

The `.axiom/toolchain.toml` pin identifies the fork-owned, unsigned
`jp-wave1-2017-04-01-v0-2-0` experimental corpus object. It is deliberately not
represented as an Axiom Foundation signed corpus release and cannot satisfy the
protected canonical apply path.

`data/coverage/tax-benefit-source-map.json` is the authoritative implementation
status ledger. A `v1.0.0` release remains gated on complete Wave 1 encoding,
independent oracle comparison, fork-owned signed apply manifests, and a
Japanese-language review.
