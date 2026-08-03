# Requirement Architecture

AMACS separates a capability concept from the conditions used to judge fit. A structured RFx requirement references a stable requirement type and, where applicable, a capability, property, credential, evidence type, response section, and decision factor.

## Requirement types

The initial registry distinguishes capability, credential, experience, geography, capacity, delivery condition, evidence, technical specification, commercial, and site/location requirements. These dimensions must not be collapsed into one free-text capability field.

## Decision treatment

Each requirement declares one treatment:

- `gate_only` — minimum compliance; no comparative points for the same fact.
- `scored_only` — comparative assessment without a minimum gate.
- `gate_and_scored_depth` — minimum coverage is mandatory and strength beyond the minimum is scored.
- `informational_only` — requested for context but not used to determine fit or selection.

## Requirement bundles

Bundles are reusable starting combinations offered in the issuer interface. They instantiate editable requirement items while preserving stable references to response sections and decision factors. Issuers may add, remove, or change items subject to readiness validation.

A bundle is not an automatic legal specification, universal qualification rule, or substitute for issuer judgment.
