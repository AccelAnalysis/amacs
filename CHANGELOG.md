# Changelog

All notable AMACS changes will be documented here.

## [0.5.0] - 2026-08-08

### Added

- Added a `MarketNeed` runtime contract that separates source statement, observed condition, desired outcome, success measures, geography, timing, commercial context, constraints, known facts, assumptions, unresolved questions, required outputs, and solution posture.
- Added provider-neutral interpretation-record and interpretation-candidate contracts for seller capability declaration, buyer need definition, provider service definition, request structuring, evidence linking, response assistance, and outcome classification.
- Added an explicit `authoritative_effect: none` boundary and mandatory human-confirmation flag for interpretation records and candidates.
- Added a governed concept-interpretation-guidance contract for inclusion notes, exclusion notes, example activities, example outputs, commonly confused capabilities, and clarification questions.
- Added examples and regression tests covering demand-side needs, supply-side capability interpretation, provider neutrality, release packaging, and the distinction between suggestions and authoritative market records.
- Added canonical need-and-interpretation architecture documentation, including manual fallback and provisional-term pathways.

### Changed

- Advanced the governed development release from `0.4.0` to `0.5.0` without changing the IDs, hierarchy, meaning, or introduction version of the existing 615 capabilities.
- Clarified that desired outcomes are target states and remain distinct from post-delivery outcome observations.
- Clarified that AI or other assistance may interpret and propose, while AMACS defines and constrains, the participant confirms, and the implementing system creates the authoritative record.
- Extended historical-meaning rules to market needs, interpretation records, candidates, and concept-guidance changes.

### Boundaries

- AMACS 0.5.0 does not select or call an AI provider, store provider credentials, prescribe model names, or make model output authoritative.
- Accepting an interpretation candidate does not itself create a capability assertion, RFx requirement, qualification decision, or taxonomy change.
- Implementations must retain a manual path and must allow provisional terms when no canonical concept fits accurately.

## [0.4.0] - 2026-08-07

### Added

- Added a governed market-role registry that separates how an organization participates in a market from how it participates on an RFx delivery team.
- Added 18 market roles spanning production, service delivery, operations, distribution, platforms, finance, risk assumption, asset ownership, development, information, intellectual property, and demand-side participation.
- Added an explicit organization capability evidence contract with entity scope, entity relationship, source authority, document hosting, validity, verification status, and provenance.
- Added 12 governed outcome types covering completion, timeliness, quality, effectiveness, financial value, adoption, stakeholder experience, safety/risk, compliance, sustainability, resilience, and innovation/improvement.
- Added an outcome-observation contract connecting post-decision results to request, response, decision, organization, capability, evidence, and measurement context.
- Added an explicit outcome-learning gate so observed outcomes cannot automatically modify capability assertions, matching behavior, or canonical AMACS content.
- Added the Fortune 100 deep market-architecture validation workflow and research contracts.

### Changed

- Extended organization capability assertions, backward-compatibly, with optional organization-identity reference, entity scope, governed market-role references, and explicit evidence references.
- Advanced the governed development release from `0.3.0` to `0.4.0` without changing the meaning or introduction version of existing capabilities.
- Made release-builder regression tests derive the current release version and release date from canonical source files instead of hard-coding `0.3.0`.

### Findings

- The Fortune 500 evidence-depth pass completed exactly ranks 1–500 and showed that the principal remaining deficiencies were structural: external-classification crosswalks, organization identity, evidence provenance, and operating-segment scope rather than another broad absence of capability vocabulary.
- The Fortune 100 stress test identified five baseline architectural gaps in 0.3.0: entity-scoped capability where segment/subsidiary structure matters, market-role representation, explicit evidence linkage, outcome architecture, and an outcome-learning guardrail.
- Existing requirement, response, and decision architectures remained suitable for the Fortune 100 architecture tests and were retained rather than replaced.

## [0.3.0] - 2026-08-05

### Added

- Added a governed Fortune 1000 organization-corpus validation method with source hashing, complete-label mapping, schema validation, and generated non-assertive observations.
- Added an organization taxonomy observation schema that separates research, evidence, entity scope, confidence, and candidate mappings from production organization capability assertions.
- Added additive domain-extension source support so later releases can expand existing domains without rewriting original concept provenance.
- Added 25 families and 115 draft capabilities covering enterprise manufacturing, finance, insurance, energy, utility, retail, digital platform, communications, media, transportation, wholesale, health-plan, care-facility, real estate, primary-production, outsourcing, education, and memorial operations.
- Added an evidence-backed 2026 Fortune 1000 breadth report and reviewed coverage summary.
- Added a controlled `RELEASE_DATE` source so generated manifests carry the applicable release date rather than a stale hard-coded value.

### Changed

- Advanced the governed development release from `0.2.0` to `0.3.0` without changing the meaning or introduction version of existing concepts.
- Expanded the taxonomy from 95 to 120 families and from 500 to 615 matchable capabilities.

### Findings

- At the primary-activity level, AMACS 0.2.0 directly covered 154 of 1,000 organizations; 524 were partial and 322 had no direct concept.
- The candidate 0.3.0 expansion provides at least one direct candidate concept for all 74 source activity labels while creating zero organization capability assertions.

## [0.2.0] - 2026-08-05

### Added

- Added the Standards, Taxonomy and Market Architecture domain.
- Added explicit matchable capabilities for taxonomy development, standards governance, capability mapping, evidence architecture, response architecture, decision architecture, controlled taxonomy licensing, and taxonomy API delivery.
- Added three browseable capability families separating standards engineering, market architecture, and licensing/API delivery.
- Added governed relationships connecting the new capabilities into common commercial delivery combinations.
- Added regression coverage for the new identifiers, hierarchy, version provenance, relationships, and release counts.
- Added commercial-capability guidance distinguishing AMACS operating machinery from AMACS-classified market services.

### Changed

- Advanced the governed development release from `0.1.0` to `0.2.0` without modifying the immutable `0.1.0` release.

## [0.1.0] - 2026-08-03

### Added

- Added controlled requirement-type and requirement-bundle registries.
- Added governance profiles separating request purpose from procedural authority.
- Added publication-readiness rules with exact deep-link targets.
- Added controlled units and property-to-unit constraints.
- Connected runtime capability requirements to response sections and decision factors.
- Foundational AMACS governance, identifiers, schemas, and validation.
- Original market-domain, family, and matchable-capability seed.
- Capability property and credential/evidence registries.
- RFx request-family registry.
- Standard response sections and common response architecture templates.
- Standard decision factors and common decision architecture templates.
- Organization-capability and RFx-requirement integration schemas.
- CSV and Excel review exporters and release builder.
- Continuous integration and structural tests.

### Known limitations

- Capability definitions are development drafts pending domain-specialist review.
- External standards crosswalks are intentionally not populated in this release.
- Multilingual labels are not yet included.
- The taxonomy is broad but not intended to be exhaustive.
