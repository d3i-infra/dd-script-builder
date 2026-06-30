# ADR 0012 — Pre-existing output dir wiped before build

**Status:** Accepted. Source: conversation.

## Decision

Before running `pnpm run release`, the service deletes the
`output_dir` subdirectory (default `releases/`) inside the build's
temp dir if it already exists. This removes any release artifacts
that were present in `TASK_SOURCE` at copy time.

## Implication

The zip artifact contains only files produced by the current build,
never stale artifacts inherited from `TASK_SOURCE`. Do not remove
this step — without it, pre-existing release files would silently
contaminate the output.
