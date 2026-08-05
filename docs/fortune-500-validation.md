# Fortune 500 evidence-depth validation

## Purpose

The Fortune 500 stage revisits the first 500 records from the governed 2026 Fortune 1000 corpus. It does not repeat the primary-industry breadth classification. It tests whether AMACS can represent the activities disclosed by reporting entities and whether the observation model can preserve legal-entity, operating-segment, subsidiary, brand, affiliate, and platform relationships.

## Automated pass

The analyzer:

1. verifies the pinned Fortune 1000 source and selects exactly ranks 1–500;
2. resolves likely SEC reporting entities using exact normalization, compact-name matching, controlled overrides, and conservative fuzzy candidates;
3. distinguishes resolved, candidate, ambiguous, and unresolved entity matches;
4. locates the latest annual filing for resolved SEC registrants;
5. optionally retrieves the filing and extracts bounded business and segment statements without storing the complete filing;
6. creates research-only records and a recurring-language gap report; and
7. emits no organization capability assertions.

Run the catalog and filing pass with:

```bash
python scripts/analyze_fortune_500.py \
  --output dist/research/fortune-500-2026 \
  --fetch-filings \
  --max-filings 500
```

## Review batches

The output is reviewed in ten rank batches of 50 organizations. Review priority is increased for:

- unresolved or ambiguous reporting entities;
- conglomerates and organizations with several reportable segments;
- statements that produce no candidate AMACS mapping;
- recurring market-activity phrases absent from preferred labels and aliases;
- parent, segment, subsidiary, affiliate, or platform relationships that cannot be represented cleanly; and
- activities that appear to require a new property, role, evidence type, or relationship rather than a new capability.

## Promotion rule

Frequency identifies where to look; it does not authorize a new concept. A proposed AMACS refinement must be semantically distinct, reusable outside the Fortune corpus, placed in the correct hierarchy, defined in original AMACS language, and reviewed under the normal release process.
