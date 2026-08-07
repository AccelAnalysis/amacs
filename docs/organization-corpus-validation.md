# Organization Corpus Validation

## Purpose

Known-organization corpora test whether AMACS can represent what organizations actually produce, operate, distribute, finance, or deliver. They are taxonomy-development inputs, not organization endorsements, credential checks, or production profile imports.

## Nested review sequence

The Fortune cohorts are nested, so each stage adds depth rather than repeating the same analysis.

### Stage 1 — Fortune 1000 breadth

- Process all 1,000 current organizations.
- Use the source's primary activity only to identify candidate AMACS concepts and broad coverage gaps.
- Preserve source version, retrieval date, and content hash.
- Generate low-confidence, machine-triage observations marked `not_for_profile_import: true`.
- Add original AMACS concepts only when the missing distinction is a market capability rather than a property, credential, scale, geography, or temporary label.

### Stage 2 — Fortune 500 evidence depth

- Revisit positions 1–500 in bounded review batches.
- Resolve the reporting entity, legal entities, operating segments, subsidiaries, and brands relevant to each observed activity.
- Use first-party company websites, annual reports, and regulatory filings for primary and secondary market activities.
- Distinguish direct performance from controlled-subsidiary, operating-segment, affiliate, and platform-participant relationships.
- Review candidate mappings, definitions, aliases, hierarchy placement, and recurring gaps.

### Stage 3 — Fortune 100 architecture depth

- Revisit positions 1–100 at the deepest level.
- Test multi-segment and conglomerate representation, evidence sufficiency, recency, provenance, capability combinations, product-versus-service boundaries, and operating-role distinctions.
- Test how the identified capabilities connect to AMACS requirements, response architecture, decision architecture, and outcome learning.
- Require analyst review and appropriate domain review before promoting any new concepts beyond draft maturity.

## Observation versus assertion

An `organization-taxonomy-observation` asks whether AMACS has language capable of representing a publicly observed activity. It may use category proxies and analyst inference because its purpose is taxonomy research.

An `organization-capability` assertion states that an identified organization possesses a capability. It requires a separate authority, evidence, and verification path. Corpus observations must never be converted automatically into assertions.

## Running the breadth pass

```bash
python scripts/analyze_organization_corpus.py \
  --output dist/research/fortune-1000-2026
```

The analyzer:

1. retrieves the external roster without vendoring it;
2. rejects an unexpected source hash unless drift is explicitly reviewed;
3. requires exactly 1,000 unique positions and a complete activity-label map;
4. verifies every candidate identifier against the current AMACS capability registry;
5. validates all generated observations against the research schema; and
6. writes a generated JSONL observation corpus and coverage summary under `dist/`.

## Refinement controls

- Frequency raises review priority but does not determine semantic quality.
- A unique high-consequence activity may justify a concept even if it appears once.
- Compound and catch-all source labels require organization-specific evidence before exact mapping.
- A corpus-specific catch-all mapping must be restricted to the reviewed organization identity so source drift cannot apply it to a different organization.
- Corporate ownership does not by itself establish direct delivery capability.
- External ranking or industry labels are not imported as canonical AMACS definitions.
- New 0.x concepts remain draft until applicable domain review.
