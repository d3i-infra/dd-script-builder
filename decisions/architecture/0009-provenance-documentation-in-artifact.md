# ADR 0009 — Provenance documentation written into every artifact

**Status:** Accepted. Source: conversation.

## Decision

Before zipping, a `documentation.txt` file is written into the
output directory. It contains the caller-supplied `documentation`
string plus the git commit hash of `TASK_SOURCE` at build time.

## Implication

Every zip artifact carries its own provenance. Do not remove or
skip the `documentation.txt` step. The commit hash is captured
with `git rev-parse HEAD` on `TASK_SOURCE`; if git is unavailable
it falls back to `"unknown"` rather than failing the build.
