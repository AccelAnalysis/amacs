# AMACS

**AMACS** is the **Accel Market Activity and Capability Standard**.

AMACS is an extensible, versioned system of taxonomies, registries, properties, relationships, and governance rules for representing:

- market needs and organizational capabilities;
- organization identity, entity scope, and market roles;
- capability qualifiers, credentials, and evidence;
- RFx request families;
- response architecture;
- decision architecture;
- outcomes and governed market learning; and
- location and site-selection factors.

The RFxchange is the first production implementation of AMACS. AMACS supplies the common language that lets a requirement created by an issuer remain connected to organization identities, capability assertions, evidence, potential matches, team gaps, response components, evaluation factors, decisions, and transaction outcomes.

## Current release

`0.4.0` is a **governed development release**, not a finished universal classification standard. It establishes the governed data model and seeds:

- 16 market domains;
- 120 capability families;
- 615 matchable capabilities;
- 185 English search aliases;
- 18 governed market roles;
- 35 reusable properties and 27 controlled units;
- 17 credential/evidence types;
- 10 requirement types and 8 reusable requirement bundles;
- 10 RFx request families and 7 governance profiles;
- 29 response sections and 7 response templates;
- 22 decision factors and 7 decision templates;
- 12 governed outcome types; and
- 30 publication-readiness rules with field-level fix targets.

Release `0.3.0` expanded capability breadth after review of the current 2026 Fortune 1000, adding 25 families and 115 draft capabilities for recurring enterprise market activities that were previously absent or only partially represented.

Release `0.4.0` is the architecture-depth refinement identified through the Fortune 500 and Fortune 100 validation stages. It adds governed external-classification crosswalk and organization-identity models, separates market role from RFx team-delivery role, supports entity-scoped capability assertions and explicit capability-to-evidence references, separates evidence authorship from document hosting, and introduces governed outcome types plus an outcome-observation contract with an explicit aggregate-learning approval gate.

The Fortune validation program remains research-only. Rankings, industry labels, public documents, lexical mappings, parent-company relationships, and outcome observations do not automatically become organization capability assertions, AMACS aliases, or canonical taxonomy changes.

All seeded capability definitions are original AMACS development content. Capability records marked `editorial_maturity: draft` require domain review before AMACS 1.0.

## Authority model

```text
Git source and schemas
→ pull-request review
→ validation and tests
→ versioned AMACS release
→ RFxchange/runtime implementation
→ governed evidence and outcome observations
→ reviewed aggregate learning
→ future AMACS proposals and releases
```

The canonical source is the version-controlled content under `source/` and `schemas/`. Compact domain and alias seeds remove repeated boilerplate while preserving stable IDs; CI deterministically expands them into ordinary JSONL release records. Excel and CSV files are generated derivatives and are not authoritative.

## Repository map

- `source/domain-seeds/` — compact canonical domain, family, and capability seeds.
- `source/domain-extensions/` — additive, versioned families and capabilities attached to existing domains without rewriting their original provenance.
- `source/alias-seed.json` — compact canonical search-language seed.
- `source/market-roles.jsonl` — governed descriptions of how organizations participate in markets, distinct from RFx team-delivery roles.
- `source/outcome-types.jsonl` — governed post-decision and post-delivery outcome categories.
- Other `source/` records — canonical JSON Lines registries.
- Release and review builds deterministically expand the compact seeds into ordinary concept and alias records.
- `schemas/` — JSON Schema contracts, including organization identity, crosswalk, evidence, capability, and outcome runtime objects.
- `docs/` — architecture, governance, editorial, and release policy.
- `research/` — reproducible non-production validation corpora and findings.
- `scripts/` — validation, release building, corpus analysis, and review export tools.
- `tests/` — structural, referential, release, and research regression tests.
- `crosswalks/` — policy and future lawful mappings to external standards.
- `examples/` — example RFxchange/runtime integration payloads.

## Development commands

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate.py
python -m unittest discover -s tests
python scripts/export_csv.py --output dist/csv
python scripts/export_excel.py --output dist/AMACS-0.4.0-review.xlsx
python scripts/build_release.py --output dist/release
python scripts/analyze_organization_corpus.py --output dist/research/fortune-1000-2026
```

Or run:

```bash
make check
make review
make release
```

## Critical boundaries

- An AMACS concept is a controlled market term, **not evidence that an organization possesses that capability**.
- Organization identity, market role, capability, evidence, RFx delivery role, and outcome are distinct objects or dimensions.
- A profile capability assertion may be self-reported, evidence-supported, or verified; evidence status alone does not substitute for an evidence record when provenance matters.
- A research corpus observation is not a profile capability assertion and cannot be imported as one.
- External classifications are governed crosswalk inputs, not automatic AMACS aliases.
- Parent ownership does not automatically attribute a subsidiary or operating-segment capability to the reporting parent.
- Capability, credential, experience, geography, capacity, delivery condition, evidence, specification, commercial, and site requirements remain distinct structured dimensions.
- A potential match is not universal qualification, endorsement, or a prediction of award.
- An outcome observation does not automatically change a capability assertion, matching behavior, or canonical AMACS content; aggregate learning requires explicit governance approval.
- Paid membership, sponsorship, or founding status cannot satisfy substantive capability requirements.
- User-proposed terms do not become canonical until governed review and release.

## Copyright and licensing

Copyright © 2026 Accel Analysis Business Solutions. All rights reserved. See [LICENSE.md](LICENSE.md). No third-party protected taxonomy is copied into this repository. External mappings may be added only after source, version, attribution, and licensing review.

## Development-release scope

AMACS 0.4.0 is deliberately broad enough to exercise production integration while remaining a governed development release. It does not claim exhaustive universal coverage. Domain definitions, aliases, lawful external crosswalks, multilingual labels, domain review, and additional evidence-backed proposals will continue through reviewed releases.
