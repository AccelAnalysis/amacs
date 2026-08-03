# AMACS

**AMACS** is the **Accel Market Activity and Capability Standard**.

AMACS is an extensible, versioned system of taxonomies, registries, properties, relationships, and governance rules for representing:

- market needs and organizational capabilities;
- capability qualifiers, credentials, and evidence;
- RFx request families;
- response architecture;
- decision architecture; and
- location and site-selection factors.

The RFxchange is the first production implementation of AMACS. AMACS supplies the common language that lets a requirement created by an issuer remain connected to organization profiles, potential matches, team gaps, response components, evaluation factors, and transaction outcomes.

## Current release

`0.1.0` is a **development foundation**, not a finished universal classification standard. It establishes the governed data model and seeds:

- 15 market domains;
- 92 capability families;
- 492 matchable capabilities;
- 185 English search aliases;
- 35 reusable properties and 27 controlled units;
- 17 credential/evidence types;
- 10 requirement types and 8 reusable requirement bundles;
- 10 RFx request families and 7 governance profiles;
- 29 response sections and 7 response templates; and
- 22 decision factors and 7 decision templates; and
- 30 publication-readiness rules with field-level fix targets.

All seeded capability definitions are original AMACS development content. Capability records marked `editorial_maturity: draft` require domain review before AMACS 1.0.

## Authority model

```text
Git source and schemas
→ pull-request review
→ validation and tests
→ versioned AMACS release
→ RFxchange runtime import
→ generated Excel and CSV review artifacts
```

The canonical source is the version-controlled content under `source/` and `schemas/`. Compact domain and alias seeds remove repeated boilerplate while preserving stable IDs; CI deterministically expands them into ordinary JSONL release records. Excel and CSV files are generated derivatives and are not authoritative.

## Repository map

- `source/domain-seeds/` — compact canonical domain, family, and capability seeds.
- `source/alias-seed.json` — compact canonical search-language seed.
- Other `source/` records — canonical JSON Lines registries.
- Release and review builds deterministically expand the compact seeds into ordinary concept and alias records.
- `schemas/` — JSON Schema contracts.
- `docs/` — architecture, governance, editorial, and release policy.
- `scripts/` — validation, release building, and review export tools.
- `tests/` — structural and referential tests.
- `crosswalks/` — policy and future lawful mappings to external standards.
- `examples/` — example RFxchange integration payloads.

## Development commands

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate.py
python -m unittest discover -s tests
python scripts/export_csv.py --output dist/csv
python scripts/export_excel.py --output dist/AMACS-0.1.0-review.xlsx
python scripts/build_release.py --output dist/release
```

Or run:

```bash
make check
make review
make release
```

## Critical boundaries

- An AMACS concept is a controlled market term, **not evidence that an organization possesses that capability**.
- A profile capability assertion may be self-reported, evidence-supported, or verified.
- Capability, credential, experience, geography, capacity, delivery condition, evidence, specification, commercial, and site requirements remain distinct structured dimensions.
- A potential match is not universal qualification, endorsement, or a prediction of award.
- Paid membership, sponsorship, or founding status cannot satisfy substantive capability requirements.
- User-proposed terms do not become canonical until governed review and release.

## Copyright and licensing

Copyright © 2026 Accel Analysis Business Solutions. All rights reserved. See [LICENSE.md](LICENSE.md). No third-party protected taxonomy is copied into this repository. External mappings may be added only after source, version, attribution, and licensing review.

## Foundation scope

AMACS 0.1.0 is deliberately broad enough to exercise production integration while remaining a governed development release. It does not claim exhaustive universal coverage. Domain definitions, aliases, lawful external crosswalks, multilingual labels, and additional user-derived proposals will expand through reviewed releases.
