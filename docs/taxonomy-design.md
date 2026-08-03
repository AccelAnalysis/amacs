# Taxonomy Design Rules

## Hierarchy

The initial navigation hierarchy is:

`Domain → Family → Capability`

Only capability records are matchable. Domains and families organize discovery and inherited properties.

## Stable identifiers

Identifiers are opaque and never encode hierarchy. Moving a concept does not change its ID. Retired identifiers are never reused.

## Class versus property

Create a capability when the concept describes a distinct service, product-producing ability, technical function, or operational function.

Create a property when the distinction is scale, geography, timing, role, delivery method, evidence, environment, capacity, or another attribute that can apply to many capabilities.

For example, AMACS stores `Commercial electrical installation` as a capability and represents two-hour emergency mobilization, service radius, project range, and license requirements as properties or credentials.

## Definitions

Definitions should:

- describe the market capability rather than promote it;
- distinguish the concept from adjacent concepts;
- avoid organization-specific wording;
- avoid embedding geography or temporary regulation;
- remain understandable to issuers and responders; and
- support translation without relying on idiom.

## Editorial maturity

- `draft` — structurally valid seed requiring domain review.
- `reviewed` — reviewed for placement and practical meaning.
- `approved` — accepted for stable release use.
