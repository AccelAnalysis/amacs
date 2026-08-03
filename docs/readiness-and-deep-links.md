# Publication Readiness and Deep Links

Publication readiness is a machine-readable rules registry. Each finding includes a severity, condition code, message, rationale, and exact `fix_target`.

The RFxchange should use that target to:

1. open the affected builder stage and section;
2. focus and visibly highlight the field;
3. display the reason beside the field;
4. preserve all previously entered work;
5. return the user to the same readiness result; and
6. re-evaluate the finding immediately after correction.

Severity states are `blocking`, `warning`, and `advisory`. Blocking findings cannot be acknowledged away. A warning may be acknowledged only when the rule permits it.
