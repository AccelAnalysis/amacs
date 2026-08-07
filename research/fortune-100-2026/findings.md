# Fortune 100 2026 architecture-validation findings

## Completion

The Fortune 100 stage is complete for the current 2026 ranking. The governed workflow produced exactly 100 schema-valid organization market-architecture reviews covering ranks 1 through 100 with no missing or duplicate ranks and zero production capability assertions.

The cohort contains 39 external primary-activity labels. Sixty-one organizations are represented by compound or catch-all activity categories, and 36 organizations have more than one candidate AMACS capability before deeper organization-specific evidence is considered. This confirms that a single industry label is not an adequate representation of a complex enterprise.

## Identity and first-party evidence

All 100 organizations reached an identity disposition suitable for architecture research:

- 92 were resolved through the governed regulatory-identity path; and
- 8 non-listed, mutual, or private structures were reviewed through current first-party source overrides.

The eight first-party override organizations are State Farm Insurance, New York Life Insurance, Nationwide, Publix Super Markets, USAA, TIAA, Liberty Mutual Insurance Group, and Massachusetts Mutual Life.

Across the bounded automated evidence path and the curated override path:

- 21 organizations had attributable annual-report evidence reviewed by the inherited Fortune 500 evidence process;
- 8 additional organizations had current first-party override evidence reviewed;
- 70 organizations reached the bounded `fortune500_evidence_unavailable` disposition; and
- 1 organization remained an evidence-extraction exception.

Evidence unavailable is a research limitation, not a capability conclusion. It does not mean that the organization lacks first-party evidence or the observed capability.

The automated evidence path identified 34 operating segments across 7 Fortune 100 organizations. Combined with the eight first-party override organizations whose corporate structures also require entity-scope distinctions, 15 of 100 organizations demonstrated why parent, subsidiary, segment, and related entity scope must be explicit.

## Baseline AMACS 0.3.0 gaps

The Fortune 100 stress test identified five recurring structural deficiencies in the 0.3.0 architecture:

| Baseline gap | Organizations affected |
|---|---:|
| Governed market-role representation | 100 |
| Explicit capability-to-evidence linkage | 100 |
| Outcome architecture | 100 |
| Outcome-learning guardrail | 100 |
| Entity-scoped capability assertion needed by observed structure | 15 |

The existing requirement, response, and decision architectures remained suitable for the test and did not require replacement.

## AMACS 0.4.0 refinements

The Fortune 100 exercise established the following governed refinements:

1. **Market-role registry.** AMACS now distinguishes how an organization participates in a market from how it participates on a particular RFx delivery team. Eighteen governed roles cover production, service, operation, retail/distribution, transportation, platform operation, infrastructure operation, insurance/risk, lending, financial intermediation, asset management, asset ownership, development, media, licensing, and demand-side participation.
2. **Entity-scoped capability assertions.** Organization capability assertions may reference the resolved organization identity and the reporting entity, legal entity, operating segment, subsidiary, brand, or unknown scope to which the assertion applies.
3. **Explicit capability evidence.** Capability assertions may reference separate evidence records that preserve source type, authoring organization, document host, entity scope, evidence locator, validity, verification status, and provenance.
4. **Outcome-type registry.** Twelve governed outcome categories cover completion, timeliness, quality/conformance, effectiveness, financial value, adoption, stakeholder experience, safety/risk, compliance, sustainability, capacity/resilience, and innovation/improvement.
5. **Outcome observations.** Post-decision and post-delivery results can be connected to requests, responses, decisions, engagements, organizations, capabilities, evidence, measurements, and targets without becoming capability assertions.
6. **Outcome-learning governance.** Outcome observations must move through explicit learning states. No individual outcome can automatically modify matching, capability status, or canonical AMACS content.

## Post-refinement result

All nine architecture tests were represented for all 100 organizations under the 0.4.0 candidate architecture:

- organization identity and entity scope — 100/100 represented;
- capability representation — 100/100 represented;
- market-role representation — 100/100 represented;
- capability-evidence linkage — 100/100 represented;
- requirement architecture — 100/100 represented;
- response architecture — 100/100 represented;
- decision architecture — 100/100 represented;
- outcome architecture — 100/100 represented; and
- outcome-learning guardrail — 100/100 represented.

After the structural refinements, the remaining review signals were nonstructural:

- 70 evidence-availability limitations from the bounded automated retrieval method;
- 1 capability-granularity review, Allstate at rank 64; and
- 29 organizations with no remaining signal under the tested architecture.

The Allstate signal is retained for semantic/domain review rather than being converted automatically into a new capability. Frequency and lexical mismatch do not authorize taxonomy expansion.

## Conclusion

The three nested Fortune stages produced different classes of AMACS improvement:

- **Fortune 1000:** expanded capability breadth where major market activities were missing.
- **Fortune 500:** established organization identity, external-classification crosswalk, evidence provenance, and operating-segment scope.
- **Fortune 100:** closed the market-role, entity-scoped capability, explicit evidence-linkage, outcome, and governed-learning architecture gaps.

The result is not evidence that AMACS has become a universal finished standard. It is evidence that the current architecture can represent the tested Fortune 100 organizations without collapsing industry category, organization identity, capability, market role, evidence, delivery role, decision, and outcome into one field. Further refinement should now be driven by domain review, evidence-backed edge cases, real RFxchange usage, and additional diverse organization corpora rather than another undirected capability expansion.
