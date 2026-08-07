# Fortune 500 taxonomy-depth validation

## Purpose

The Fortune 500 stage revisits the first 500 records from the governed 2026 Fortune 1000 corpus. It does not repeat the primary-industry breadth classification. It tests whether AMACS can preserve external classification semantics, resolve organization identity without forcing false matches, and distinguish taxonomy observations from organization capability assertions.

## Automated pass

The governed workflow:

1. verifies the pinned Fortune 1000 source and selects exactly ranks 1–500;
2. resolves likely reporting entities using exact normalization, compact-name matching, controlled overrides, current and former regulatory names, and conservative fuzzy candidates;
3. distinguishes resolved, candidate, ambiguous, and unresolved entity matches;
4. carries CIK, ticker, SIC, entity type, and exchange metadata only when a reporting entity is resolved;
5. maps external primary-activity categories and SEC-derived SIC descriptions to low-confidence AMACS candidates;
6. transforms every raw record into the organization taxonomy observation schema;
7. emits separate external-classification crosswalk and organization-identity candidates; and
8. validates that no external category becomes an AMACS alias and no organization profile or capability assertion is created.

The regulatory metadata source is a pinned third-party mirror built from the SEC submissions bulk archive. Every generated record preserves that source chain. The mirror is not represented as an SEC-hosted source.

Run the complete pass with:

```bash
python scripts/run_fortune_500.py \
  --source-file /path/to/fortune-1000-2026.json \
  --listed-metadata-file /path/to/listed_filer_metadata.csv.gz \
  --listed-names-file /path/to/listed_filer_names.csv.gz \
  --output dist/research/fortune-500-2026

python scripts/govern_fortune_500_artifacts.py \
  --input-dir dist/research/fortune-500-2026
```

## Completed results

The governed pass processed all 500 organizations and produced:

- 433 resolved reporting entities, including 430 automatic matches and 3 controlled overrides;
- 8 ambiguous, 10 candidate, and 49 unresolved identities;
- 65 external primary-activity labels;
- 33 compound or catch-all labels;
- 31 labels that map to more than one AMACS capability;
- 112 draft external-classification crosswalk candidates;
- 500 draft organization-identity candidates;
- 426 observations requiring crosswalk treatment;
- 67 observations requiring identity resolution; and
- 7 simple category observations that still lack capability-level evidence.

All 500 observations, all 112 crosswalk candidates, and all 500 identity candidates pass their schemas. Zero external categories are imported as aliases, zero organization profiles are created, and zero organization capability assertions are created.

## AMACS refinements established by the pass

### External classification crosswalks

An external industry, commodity, occupation, regulatory, or ranking category is not automatically an AMACS synonym. The crosswalk model records the source scheme, source entry, target capability, mapping relation, confidence, rationale, provenance, and review status. It supports exact, close, broad, narrow, and related mappings without contaminating governed AMACS aliases.

### Organization identity

AMACS now has a model for legal, regulatory, trade, acronym, former, ranking-display, segment, subsidiary, and brand identities. It also separates external identifiers and entity relationships from capability assertions. This is required for organizations represented by acronyms, former names, mutual structures, brands, reporting entities, or operating segments.

### Semantic mapping safeguards

SIC descriptions and other external labels are taxonomy evidence, not capability evidence. Lexical overlap can generate false candidates; for example, words such as hospital, construction, or real estate may describe a regulatory category without proving the corresponding AMACS capability. These mappings therefore remain low-confidence, relationship-unknown observations pending semantic and domain review.

## Remaining evidence layer

Live SEC endpoints denied requests from GitHub-hosted runners during this pass. The current automated corpus therefore completes reporting-entity resolution and taxonomy-depth analysis using the pinned SEC-derived metadata mirror, but it does not claim to have completed annual-filing business-section and operating-segment extraction. First-party filing and annual-report evidence remains a separate governed review layer and must not be inferred from SIC metadata.

## Review batches

The 500 records remain organized in ten rank batches of 50. Review priority is increased for:

- unresolved or ambiguous identities;
- conglomerates and organizations with several reportable segments;
- external categories that map to several AMACS concepts;
- SIC candidates that conflict with the primary-activity mapping;
- parent, segment, subsidiary, affiliate, or platform relationships that cannot yet be represented cleanly; and
- activities that appear to require a new property, role, evidence type, or relationship rather than a new capability.

## Promotion rule

Frequency identifies where to look; it does not authorize a new concept. A proposed AMACS refinement must be semantically distinct, reusable outside the Fortune corpus, placed in the correct hierarchy, defined in original AMACS language, and reviewed under the normal release process.
