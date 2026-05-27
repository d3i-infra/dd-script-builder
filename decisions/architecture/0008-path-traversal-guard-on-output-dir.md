# ADR 0008 — Path traversal guard on output_dir

**Status:** Accepted. Source: conversation.

## Decision

Before zipping, `output_dir` is resolved with `os.realpath` and
checked to confirm it starts with the build's temp dir. Builds
that attempt to escape the temp dir (e.g. via `../`) are rejected
with a `RuntimeError`.

## Implication

Any code that resolves caller-supplied paths inside a build must
apply the same `realpath` prefix check. Do not skip or weaken
this guard.
