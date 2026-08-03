# RFxchange Integration Contract

The RFxchange should deploy an immutable AMACS release projection. Runtime records include:

- `amacs_release_id`;
- `source_commit_sha`;
- `record_checksum`; and
- `imported_at`.

Production administrators may review deployed records and proposals, but they must not permanently alter canonical AMACS records in Firestore. Approved changes return through Git and a versioned AMACS release.

## Organization capability assertion

An organization selects a capability, delivery roles, service geography, operating properties, and evidence status. The concept ID standardizes matching; narrative remains available for explanation.

## RFx requirement

The issuer selects a capability and adds requirement level, qualifiers, evidence, team-coverage permission, and decision treatment. Every structured requirement should carry into responder compliance and, where applicable, issuer evaluation.

## Search and matching language

The platform may search preferred labels, aliases, related concepts, and provisional terms. Search expansion is not the same as requirement satisfaction.
