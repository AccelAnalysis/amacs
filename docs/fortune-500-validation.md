# Fortune 500 taxonomy-depth and evidence validation

## Purpose

The Fortune 500 stage revisits ranks 1–500 from the governed 2026 Fortune 1000 corpus at greater depth. It does not repeat the breadth classification. It tests whether AMACS can preserve external-classification semantics, resolve organization identity without forcing false matches, represent operating-segment scope, attach first-party evidence without confusing document authorship and hosting, and distinguish taxonomy research from production capability assertions.

## Governed method

The completed workflow:

1. verifies the pinned 2026 Fortune corpus and selects exactly ranks 1–500;
2. resolves likely reporting entities using exact, compact, acronym, former-name, controlled-override, and conservative fuzzy matching against a pinned SEC-derived metadata mirror;
3. emits separate organization-identity and external-classification crosswalk candidates;
4. treats Fortune industry and SIC descriptions as crosswalk evidence rather than AMACS aliases or organization capability evidence;
5. attempts bounded review of the company-authored 2025 annual report for every resolved listed organization using a document mirror as host only;
6. verifies document attribution before extracting activity language or operating-segment observations;
7. maps extracted first-party activity statements to AMACS only as research candidates;
8. records a terminal disposition when evidence is unavailable, identity is unresolved, or safe extraction is not possible; and
9. fails completion unless every rank 1–500 has exactly one schema-valid terminal review.

No generated corpus record is eligible for direct production profile import.

## Completed results

The final completion gate passed with exactly 500 records, ranks 1–500, no missing ranks, and no duplicates.

### Organization identity

- 445 organizations resolved to a reporting identity;
- 2 remained ambiguous;
- 8 remained candidate matches; and
- 45 remained unresolved.

Unresolved identity is a valid completed research disposition. Private, mutual, cooperative, foreign, or otherwise non-listed structures are not forced into a public-company match.

### First-party evidence

- 33 attributable 2025 annual reports were reviewed;
- 32 organizations yielded extractable activity statements;
- 653 bounded first-party activity statements were captured;
- 12 organizations yielded operating-segment observations;
- 63 operating segments were identified; and
- 31 organizations produced AMACS candidate mappings from first-party activity language, totaling 330 candidate mappings.

Terminal evidence dispositions across the full cohort were:

- 32 `annual_report_reviewed`;
- 1 `annual_report_found_no_extractable_activity`;
- 410 `annual_report_unavailable`;
- 2 `evidence_error`; and
- 55 `identity_unresolved`.

`annual_report_unavailable` means the bounded automated evidence path did not locate an attributable 2025 report under the governed retrieval method. It is not a statement that the organization has no annual report or that no other first-party evidence exists.

### AMACS gap signals

The completed pass produced:

- 15 crosswalk-conflict cases, where first-party activity language diverged from the coarse external primary-activity proxy;
- 1 capability-granularity case requiring semantic review;
- 2 document-extraction/evidence-model exceptions; and
- 17 reviewed organizations with no additional structural gap signal.

The single capability-granularity case was Allstate. This is materially different from the Fortune 1000 breadth pass: at Fortune 500 depth, the dominant findings were structural rather than a broad absence of capability vocabulary.

## AMACS refinements established by the pass

### External classification crosswalks

External industry, commodity, occupational, regulatory, ranking, or similar categories are not automatically AMACS synonyms. The crosswalk model preserves source scheme, source entry, target capability, mapping relation, confidence, rationale, provenance, and review status. It supports exact, close, broad, narrow, and related mappings while explicitly prohibiting alias import.

### Organization identity

AMACS now has a research model for ranking-display, legal, regulatory, trade, acronym, former, segment, subsidiary, and brand identities, together with external identifiers and organization relationships. Identity resolution remains separate from capability assertion.

### Evidence author/host separation

A mirrored first-party document must distinguish the organization that authored or issued the evidence from the service that hosts the file. This prevents a document mirror from being misrepresented as the evidentiary authority.

### Operating-segment representation

Operating-segment activity is represented explicitly as an entity relationship rather than being attributed automatically to the parent reporting entity. The Fortune 500 pass observed 63 segments across 12 organizations and established this as a recurring structural need.

### Semantic safeguards

External classifications and lexical overlap remain taxonomy evidence, not proof of capability. The 15 crosswalk conflicts show why company-authored activity language must be allowed to disagree with a coarse industry label without either source being silently overwritten.

## Completion semantics

The Fortune 500 stage is complete because every organization reached a governed terminal review disposition, not because every organization had equal public evidence availability. Missing public evidence, unresolved identity, and safe-extraction failure remain visible limitations rather than being converted into inferred capabilities.

The Fortune 100 stage builds on this completed baseline with deeper multi-source evidence, segment/subsidiary architecture, market-role testing, capability/evidence linkage, response and decision architecture, and outcome-learning representation.

## Promotion rule

Frequency identifies where to investigate; it does not authorize a new concept. Any AMACS refinement must be semantically distinct, reusable outside the Fortune corpus, placed in the correct architecture, written in original AMACS language, and pass normal governance and domain review before production promotion.
