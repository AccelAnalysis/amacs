# Changelog

All notable AMACS changes will be documented here.

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
