# rulespec-jp

Independent, public Axiom-compatible encodings of Japanese national tax and
benefit law, with an inclusive support boundary of **2017-04-01**.

This repository is maintained under `anth-volk`. It is not an official Axiom
Foundation jurisdiction, is not listed in an Axiom lane registry, and does not
send issues, branches, pull requests, releases, or signing material upstream.

## Wave 1 status

The planned Wave 1 policy surfaces are encoded through the latest enacted rules
in the 2026-07-23 source freeze. The implementation remains an experimental,
unsigned `v0.x` model pending an independent oracle comparison and
Japanese-language legal review; it is not canonical Axiom material.

Wave 1 includes:

- ordinary domestic national income-tax residence and liability;
- employment and public-pension income, including the 2020, 2025, and enacted
  2026–2028 amendments that affect the supported path;
- the income-adjustment deduction and aggregation of supported income;
- basic, social-insurance, disability, widow/widower/single-parent,
  working-student, spouse, special-spouse, dependent, and specific-relative
  deductions;
- the seven-bracket national income-tax schedule;
- the 2024 fixed income-tax credit;
- reconstruction special income tax and the enacted 2027 defense-tax split;
- Child Allowance through the October 2024 expansion;
- Child Rearing Allowance through April 2026;
- Special Child Rearing Allowance, Disabled Child Welfare Allowance, and
  Special Disability Allowance through April 2026;
- National Pension contribution amounts through FY2026 and the statutory
  exemption and deferral routes;
- Employees' Pension worker contributions, including all 32 remuneration
  bands, bonuses, rate, employee share, and official rounding; and
- Employment Insurance worker contributions through FY2026, including the
  October 2022 split, covered wages, industry rates, and per-payment rounding.

Medical classifications and fact-intensive statutory decisions are explicit
inputs. The model does not infer disability from a diagnosis or adjudicate
custody, co-residence, financial support, or agency approval from raw evidence.

The income-tax composition is the Wave 1 path for ordinary employment and
public-pension income. Other income classes, loss offsets, and deductions or
credits assigned to Wave 3 require additional data and must be supplied as
zero when they are not modeled.

## Deliberate exclusions

No combined disposable-income output is published. Individual inhabitant tax,
National Health Insurance premiums, employee health-insurance premiums, and
long-term-care premiums are not nationally uniform enough to represent as one
Japan-wide formula.

Other explicit skips are Public Assistance cash amounts, municipal childcare
and family benefits, local housing assistance, property and other local taxes,
employer-specific benefits, corporate and business tax, and
non-deterministic emergency payments. See
`data/coverage/tax-benefit-source-map.json` for the authoritative ledger.

## Time and calendar contract

- Monthly benefits and contributions begin in April 2017. March 2017 and
  earlier months are unsupported.
- Tax Year 2017 may be evaluated as an annual liability only where the April 1
  consolidated law and NTA annual material establish the applicable rule.
- The first complete calendar-year component scenario is 2018.
- Gregorian ISO dates control ordering and execution.
- Japanese era expressions are retained verbatim in provenance. For example,
  `平成29年4月1日` normalizes to `2017-04-01`, and `平成29年度` normalizes to
  `2017-04-01/2018-03-31`.

## Repository contract

- `jp/statutes`, `jp/regulations`, and `jp/policies` contain atomic RuleSpec.
- `jp/programs` contains declarative composition requests only.
- Every atomic module has a same-stem `.test.yaml` companion.
- Every monetary parameter has an exact primary-source proof atom.
- JPY uses zero minor units.
- Original Japanese text is authoritative; English text is explanatory.

## Validation

Build the forked engine, then run:

```bash
cargo build --manifest-path ../axiom-rules-engine/Cargo.toml --locked
AXIOM_RULES_ENGINE_BIN=../axiom-rules-engine/target/debug/axiom-rules-engine \
AXIOM_COMPOSE_BIN=../axiom-compose/.venv/bin/axiom-compose \
  python3 -m pytest -q tests
```

The repository also provides:

- `scripts/validate_corpus_proofs.py` to match every cited path and exact
  excerpt against the full Japan corpus;
- a strict monetary-proof-atom repository gate;
- the official `axiom-encode test` runner;
- an oracle-pending ratchet; and
- `data/scenarios/wave1-2018-working-parent.yaml`, an end-to-end annual
  component ledger for a working parent.

The `.axiom/toolchain.toml` pin identifies the fork-owned, unsigned
`jp-wave1-2017-04-01-v0-5-0` experimental corpus manifest. It is deliberately
not represented as an Axiom Foundation signed corpus release and cannot satisfy
the protected canonical apply path.

Independent OECD TaxBEN comparison and Japanese-language legal review remain
release-quality gates for a validated stable release. They do not change the
machine-readable status of the planned Wave 1 policy surfaces.
