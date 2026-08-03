# Request, Response, and Decision Architecture

AMACS connects three registries that must not drift apart.

## Request family

The request family defines the purpose, default endpoint, lifecycle, and recommended response and decision templates. RFI, RFQ, RFP, qualifications, supplier requests, teaming requests, and site-selection projects do not share one identical screen sequence or endpoint.

## Response architecture

Response sections are atomic reusable objects. Templates are ordered combinations of those sections. An issuer may add canonical sections, alter local instructions, or create a local section without immediately changing the global library.

## Decision architecture

Decision factors separate mandatory gates from comparative evaluation. A capability requirement may be:

- gate only;
- scored only;
- gate plus scored depth; or
- informational only.

The system should warn when the same fact is counted twice, a scored factor lacks evidence, a response section is never used, or a mandatory requirement has no decision treatment.

## Readiness links

Publication-readiness findings should identify the builder section and field responsible for the issue, support keyboard focus and visible highlighting, preserve entered data, and provide a return path to the same readiness result.
