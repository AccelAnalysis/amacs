# Contributing to AMACS

## Before proposing a new concept

1. Search preferred labels and aliases.
2. Determine whether the submission is a capability, property, credential, response section, decision factor, or local wording variation.
3. Provide a plain-language definition and at least one realistic use example.
4. Identify the closest existing parent or related concept.
5. Avoid promotional claims, organization names, brand names, and combinations better represented as properties.

## Pull-request expectations

- Do not reuse identifiers.
- Keep one JSON object per line in canonical JSONL files.
- Preserve stable IDs when labels or hierarchy positions change.
- Add replacement and migration information for deprecated concepts.
- Update the changelog for user-visible changes.
- Run `make check` before opening a pull request.
- Regenerate review outputs only through the supplied scripts; generated files are not committed.

## Editorial test

A useful AMACS capability answers: **What can an organization actually provide or perform?**

A property answers: **Under what conditions, at what scale, where, how quickly, or with what evidence can it do so?**
