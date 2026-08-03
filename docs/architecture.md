# AMACS Architecture

AMACS separates semantic identity from runtime assertions.

## Canonical registries

1. **Concepts** — domains, families, and matchable capabilities.
2. **Aliases** — synonyms, abbreviations, and search language.
3. **Relationships** — related, required, commonly combined, replacement, split, and merge relationships.
4. **Properties and values** — reusable qualifiers such as geography, capacity, timing, delivery mode, and site characteristics.
5. **Credentials** — license, certification, registration, evidence, and confirmation types.
6. **Request families** — RFI, RFQ, RFP, qualification, teaming, supplier, and site-selection request structures.
7. **Response architecture** — reusable response sections and section combinations.
8. **Decision architecture** — compliance gates, scored factors, narratives, formulas, and common combinations.

## Runtime objects

AMACS does not store that a particular organization possesses a capability. The RFxchange stores an organization capability assertion that references an AMACS capability ID, release, label snapshot, properties, delivery roles, and evidence status.

An RFx capability requirement similarly references an AMACS capability ID and adds requirement level, team coverage, decision treatment, qualifiers, and required evidence.

## Matching discipline

- Exact capability match may satisfy the concept dimension.
- A narrower child may satisfy a broader parent when an approved hierarchy rule permits it.
- A broader parent does not automatically satisfy a narrower required capability.
- Properties and credentials are evaluated independently from concept identity.
- Team coverage is evaluated only when explicitly allowed.
- Self-reported capability is not the same as verified evidence.
- Matching explains fit and gaps; it does not select a winner.

## Historical meaning

Every RFx and capability assertion stores the AMACS release and label snapshot used at the time. A later rename, move, split, merge, or deprecation must not silently change the historical meaning of a published RFx.
