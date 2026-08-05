# Release Process

1. Create a change branch from the current default branch.
2. Add or modify canonical source and schemas.
3. Set `VERSION` and the ISO 8601 calendar date in `RELEASE_DATE` for the proposed release.
4. Run schema, referential, hierarchy, duplicate, template, team-coverage, and release-invariant validation.
5. Obtain required editorial and domain review.
6. Merge through pull request.
7. Tag the approved commit with the semantic version.
8. Build the immutable release directory and checksums from the approved commit.
9. Generate Excel and CSV review artifacts.
10. Import the release into the RFxchange staging environment.
11. Verify migration, search, matching, request, response, and decision behavior.
12. Promote the exact release to production.

## Source provenance

Every release manifest records a full 40-character Git commit SHA. `make release` resolves and passes the current `HEAD`; direct builds may either supply `--source-commit <full-sha>` or allow the builder to resolve `git rev-parse --verify HEAD`.

```bash
make release

# Equivalent direct command
python scripts/build_release.py \
  --output dist/release \
  --source-commit "$(git rev-parse --verify HEAD)"
```

The builder rejects missing, abbreviated, malformed, or placeholder commit values.

The manifest release date is read from the canonical `RELEASE_DATE` file and validated as an ISO 8601 calendar date. This keeps release metadata reviewable and prevents a stale date embedded in the build script.

## Immutability

The release target is `OUTPUT_ROOT/VERSION`. If that version directory already exists, the builder fails without deleting or modifying it. A release cannot be rebuilt from altered source under the same version number. Create a new semantic version for changed release content.

Generated manifests, expanded datasets, checksums, CSV exports, and Excel review workbooks belong under `dist/` and are not committed as canonical source.
