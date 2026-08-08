# Need and Interpretation Architecture

AMACS 0.5.0 adds the semantic contracts required to translate ordinary market language into governed AMACS-backed records without making an interpretation system authoritative.

## Governing principle

> AI or other assistance interprets and proposes. AMACS defines and constrains. The participant confirms. The implementing system stores and operates the authoritative record.

An interpretation is never an organization capability assertion, RFx requirement, qualification decision, or taxonomy change by itself.

## Why this layer exists

Buyers often know the condition they are experiencing and the outcome they want without knowing the correct request family or capabilities. Sellers often know what work they perform without knowing the AMACS concepts that best represent it. A usable market standard therefore needs a controlled bridge between human language and canonical market meaning.

AMACS 0.5.0 standardizes that bridge through four provider-neutral contracts:

1. `market-need.schema.json`
2. `interpretation-record.schema.json`
3. `interpretation-candidate.schema.json`
4. `concept-interpretation-guidance.schema.json`

The contracts do not call an AI model, select a provider, contain credentials, or define implementation pricing.

## Market need

A market need represents the demand-side condition that motivates market activity. It includes:

- the participant's source statement;
- the observed condition;
- the desired outcome or target state;
- affected people, assets, operations, or environments;
- success measures;
- geography and timing;
- commercial context;
- constraints;
- known facts;
- assumptions;
- unresolved questions;
- solution posture;
- prohibited approaches;
- required outputs; and
- references to interpretation and later confirmed requirement records.

A market need is not a universal taxonomy code for every possible problem. It is a runtime object owned by the implementing system and structured according to AMACS.

## Need, solution, and outcome are distinct

- **Observed condition** describes what is happening now.
- **Desired outcome** describes the state the participant wants to achieve.
- **Solution posture** establishes whether the market may propose alternatives or must respond to a defined approach.
- **Proposed solution** is one possible method, product, service, or combination.
- **Capability requirement** describes what a responding organization or team must be able to do.
- **Outcome observation** records what actually happened after a decision or delivery.

A desired outcome must not be stored as though it were an observed post-delivery outcome. A proposed solution must not be silently treated as the only valid capability pathway when the need remains solution-open.

## Interpretation record

An interpretation record groups one bounded interpretation exercise, such as:

- seller capability declaration;
- buyer need definition;
- provider service definition;
- evidence linking;
- request structure;
- response assistance; or
- outcome classification.

It records the AMACS release, source references, candidate references, method, status, and an opaque implementation-provenance reference. It has `authoritative_effect: none` and requires human confirmation.

Provider, model, prompt, token, cost, retention, and similar operational metadata remain in the implementing system's provenance record rather than the AMACS standard.

## Interpretation candidate

An interpretation candidate maps source language or evidence to a possible:

- market-need dimension;
- organization capability assertion;
- RFx capability requirement;
- request family;
- property value;
- credential requirement;
- response section;
- decision factor;
- market role; or
- provisional term.

Each candidate preserves source evidence, the proposed value, rationale, confidence, ambiguity, mapping method, and participant disposition.

Candidate dispositions are:

`Suggested → Accepted / Edited / Rejected / Unresolved / Withdrawn`

Acceptance does not itself create an authoritative record. A separate confirmed write must create the market need, capability assertion, RFx requirement, or other transaction object.

## Concept interpretation guidance

Concept guidance helps humans and interpretation systems understand a capability boundary. It can include:

- inclusion notes;
- exclusion notes;
- example activities;
- example outputs;
- commonly confused concepts; and
- clarification questions.

Guidance supports retrieval and disambiguation. It does not change concept identity, prove that an organization has the capability, or establish qualification for an RFx.

## Seller-side sequence

```text
Organization explains what it does
→ bounded interpretation record
→ candidate AMACS capabilities
→ clarification where needed
→ participant accepts, edits, or rejects
→ separate confirmed organization-capability assertions
→ evidence and verification remain separate
```

## Buyer-side sequence

```text
Issuer explains the condition and desired outcome
→ structured market need
→ bounded interpretation record
→ candidate request family and AMACS requirements
→ clarification where needed
→ issuer accepts, edits, or rejects
→ separate confirmed RFx requirements
→ publication readiness and market operation
```

## Manual path

Implementations must retain a non-AI path. A participant must be able to:

- describe a need manually;
- browse and search AMACS;
- select or remove capabilities;
- propose a provisional term;
- edit structured fields; and
- continue when an interpretation service is unavailable or disabled.

## Provisional terms

When no AMACS concept fits accurately, the participant must not be forced into an incorrect mapping. The interpretation candidate may identify a provisional term and reference a governed taxonomy proposal. The provisional term remains noncanonical until reviewed and released through AMACS governance.

## Learning boundary

Accepted and rejected candidates can improve implementation quality, but they do not automatically alter AMACS. Market needs, capability assertions, requirements, responses, decisions, and outcomes may produce governed learning signals only through the applicable approval process.

## Historical meaning

Every market need, interpretation record, candidate, capability assertion, and RFx requirement references the AMACS release used at the time. A later release must not silently reinterpret a historical transaction.
