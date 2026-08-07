# AMACS Architecture

AMACS separates semantic identity from runtime assertions, evidence, and outcomes.

## Canonical registries

1. **Concepts** — domains, families, and matchable capabilities.
2. **Aliases** — synonyms, abbreviations, and search language.
3. **Relationships** — related, required, commonly combined, replacement, split, and merge relationships.
4. **Properties and values** — reusable qualifiers such as geography, capacity, timing, delivery mode, and site characteristics.
5. **Credentials** — license, certification, registration, evidence, and confirmation types.
6. **Request families** — RFI, RFQ, RFP, qualification, teaming, supplier, and site-selection request structures.
7. **Response architecture** — reusable response sections and section combinations.
8. **Decision architecture** — compliance gates, scored factors, narratives, formulas, and common combinations.
9. **Market roles** — governed descriptions of how an organization participates in a market, distinct from RFx delivery-team role.
10. **Outcome types** — governed categories for post-decision and post-delivery results that may be observed and reviewed for market learning.

## Runtime objects

AMACS does not store that a particular organization possesses a capability as canonical taxonomy content. A runtime organization-capability assertion references an AMACS capability ID, release, label snapshot, properties, RFx delivery roles, optional market roles, optional resolved entity identity/scope, and evidence references.

An RFx capability requirement similarly references an AMACS capability ID and adds requirement level, team coverage, decision treatment, qualifiers, and required evidence.

An **organization capability evidence** record is separate from the assertion it supports. It preserves the relevant organization and entity scope, capability reference, source type, authorship, document host where applicable, evidence locator, validity, verification method, and evidence status. This prevents a boolean or status label such as “verified” from becoming a substitute for provenance.

An **outcome observation** is separate from the capability assertion and decision that preceded it. It may reference a request, response, decision, engagement, organizations, capabilities, evidence, measurement period, target, value, and verification status. Its learning status determines whether it is excluded, merely eligible for review, reviewed, or approved for aggregate learning.

## Organization identity and scope

Organization identity is not capability identity. AMACS-related runtime and research contracts can distinguish reporting entities, legal entities, operating segments, subsidiaries, brands, trade names, former names, regulatory identities, and external identifiers.

A capability observed for an operating segment or controlled subsidiary must not be silently attributed to the reporting parent. Entity scope and entity relationship remain explicit whenever the evidence or assertion is narrower than the parent organization.

## Market role versus delivery role

**Market role** describes how an organization participates in the underlying market relative to a capability—for example manufacturer, operator, retailer, distributor, platform operator, insurer, lender, asset manager, asset owner, or buyer/issuer.

**RFx delivery role** describes how a participant intends to participate in a particular delivery team—for example prime, subcontractor, supplier, or referral partner.

An organization may hold several market roles simultaneously and may use a different delivery role for a particular opportunity. These dimensions must not be collapsed.

## Matching discipline

- Exact capability match may satisfy the concept dimension.
- A narrower child may satisfy a broader parent when an approved hierarchy rule permits it.
- A broader parent does not automatically satisfy a narrower required capability.
- Properties and credentials are evaluated independently from concept identity.
- Organization/entity scope is evaluated independently from concept identity.
- Market role may qualify how a capability participates in a market but does not replace the capability itself.
- Team coverage is evaluated only when explicitly allowed.
- Self-reported capability is not the same as verified evidence.
- Evidence must be attributable to the relevant organization/entity scope when it is used to support an assertion.
- Matching explains fit and gaps; it does not select a winner.

## Outcome and learning discipline

AMACS connects decisions to outcomes without allowing outcomes to rewrite the standard automatically.

- A decision is the governed selection or evaluation result.
- An outcome is an observed post-decision or post-delivery result.
- An outcome observation can support later evaluation of performance, fit, risk, or market behavior.
- Individual outcomes do not automatically raise or lower organization capability status.
- Outcome-derived learning cannot automatically alter matching logic or canonical concepts.
- Only observations explicitly approved for aggregate learning may be considered as governed inputs to future proposals, analysis, or AMACS releases.

This creates the intended closed loop: needs → capabilities → evidence → responses → decisions → outcomes → governed learning, while preserving the authority boundaries between each layer.

## Historical meaning

Every RFx and capability assertion stores the AMACS release and label snapshot used at the time. A later rename, move, split, merge, deprecation, market-role change, or outcome-learning refinement must not silently change the historical meaning of a published RFx or past capability assertion.
