# ADR 0003 — In-memory build store, no persistence

**Status:** Accepted. Source: conversation.

## Decision

Build state is held in a single in-memory `BuildStore` (a dict
keyed by UUID). There is no database or disk-backed state. The
store is lost on process restart; all in-flight or completed
builds are gone.

## Implication

This service is stateless across restarts. Callers must download
or act on a build before the process is restarted. If persistence
is ever required, a new ADR must be written before adding it —
do not silently add a database.
