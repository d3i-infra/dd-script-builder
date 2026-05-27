# ADR 0007 — Client-managed temp dir cleanup

**Status:** Accepted. Source: conversation.

## Decision

Each build gets a `tempfile.mkdtemp` directory. Temp dirs are
**only** removed when the client explicitly calls
`DELETE /build/{id}`. The service does not auto-expire, garbage-
collect, or clean up on error.

## Implication

Uncleaned builds leak disk space indefinitely. Callers are
responsible for calling DELETE after downloading the artifact.
Do not add silent auto-cleanup without a new ADR — the current
model makes resource ownership explicit and visible via
`GET /builds`.
