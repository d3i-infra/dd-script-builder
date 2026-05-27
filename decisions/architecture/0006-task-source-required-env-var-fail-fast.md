# ADR 0006 — TASK_SOURCE is a required env var; fail fast on startup

**Status:** Accepted. Source: conversation.

## Decision

`TASK_SOURCE` (path to the source repo) is read from the
environment at import time. If it is not set the process raises
`RuntimeError` immediately and refuses to start. There is no
default or fallback.

## Implication

The service will not start without `TASK_SOURCE`. This is
intentional. Do not add a default value or a runtime check that
silently degrades. Deployment configs and tests must supply this
variable.
