# AMACS Governance

## Standards authority

Accel Analysis Business Solutions is the initial AMACS standards authority and release maintainer.

## Change authority

Canonical AMACS changes occur only through a pull request against the protected default branch. A user, RFx issuer, organization, administrator, or domain adviser may propose a change, but no proposal directly alters the standard.

## Roles

- **Maintainer** — approves releases, identifier allocation, governance, and final editorial decisions.
- **Editor** — drafts concepts, definitions, relationships, properties, templates, and migrations.
- **Domain reviewer** — evaluates accuracy, scope, terminology, and practical market use.
- **Contributor** — submits proposals, issues, evidence, and suggested mappings.
- **RFxchange importer** — consumes approved releases and has no authority to rewrite canonical records.

## Required review

A pull request changing canonical records must pass automated validation and receive approval from an authorized maintainer. Major domain changes should also receive an applicable domain review.

## Proposal states

`submitted → triaged → mapped_to_existing | approved_new | rejected | needs_information`

A provisional term may support search and editorial analysis, but it must not automatically satisfy a mandatory capability gate before canonical approval.

## Release stages

- `0.x` — governed development releases.
- `1.0.0` — first production standard approved for broad stable use.
- Minor release — backward-compatible additions and clarifications.
- Major release — potentially breaking semantic or structural change.
- Patch release — corrections that do not change intended meaning.

## Conflicts and integrity

Editors disclose material interests in concepts under review. Commercial membership, sponsorship, contribution volume, or organizational influence cannot purchase a capability definition, verification result, or preferential match treatment.
