# Release Process

1. Create a change branch from the current default branch.
2. Add or modify canonical source and schemas.
3. Run schema, referential, hierarchy, duplicate, and template validation.
4. Obtain required editorial and domain review.
5. Merge through pull request.
6. Tag the approved commit with the semantic version.
7. Build the immutable release directory and checksums.
8. Generate Excel and CSV review artifacts.
9. Import the release into the RFxchange staging environment.
10. Verify migration, search, matching, request, response, and decision behavior.
11. Promote the exact release to production.

A release cannot be rebuilt from altered source under the same version number.
