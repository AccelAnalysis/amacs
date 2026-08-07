# Canonical Source and Generated Releases

AMACS uses compact, reviewable Git source for the two largest repetitive registries:

- `source/domain-seeds/*.json` stores stable domain, family, and capability IDs and labels.
- `source/domain-extensions/<version>/*.json` adds versioned families and capabilities to an existing domain without restating or changing the base domain seed.
- `source/alias-seed.json` stores stable alias IDs and search language.

The build tooling deterministically expands those seeds into the full `concepts.jsonl` and `aliases.jsonl` datasets used in release packages, CSV exports, Excel review workbooks, and runtime imports. All other registries remain canonical JSON Lines source.

Domain extensions are additive only. An extension must reference an existing base domain, use new stable identifiers, declare its introduction version, and pass the same concept, hierarchy, duplicate, and reference validation as base seed content. Corrections to an existing concept remain explicit canonical edits subject to normal governance; extensions are not an override mechanism.

This does not make the generated files a second authority. A generated record is reproducible from a specific Git commit and AMACS version. Any definition that needs to differ from the standard generated wording can be overridden in the applicable seed record.
