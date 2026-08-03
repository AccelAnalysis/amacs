# Canonical Source and Generated Releases

AMACS uses compact, reviewable Git source for the two largest repetitive registries:

- `source/domain-seeds/*.json` stores stable domain, family, and capability IDs and labels.
- `source/alias-seed.json` stores stable alias IDs and search language.

The build tooling deterministically expands those seeds into the full `concepts.jsonl` and `aliases.jsonl` datasets used in release packages, CSV exports, Excel review workbooks, and runtime imports. All other registries remain canonical JSON Lines source.

This does not make the generated files a second authority. A generated record is reproducible from a specific Git commit and AMACS version. Any definition that needs to differ from the standard generated wording can be overridden in the applicable seed record.
