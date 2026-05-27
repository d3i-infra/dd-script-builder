# ADR 0004 — Async semaphore-bounded build execution

**Status:** Accepted. Source: conversation.

## Decision

Builds run as asyncio background tasks (`run_build`) under a
shared `asyncio.Semaphore` capped at `MAX_CONCURRENT_BUILDS` (5).
CPU-bound subprocess calls are offloaded with `asyncio.to_thread`
so the event loop stays unblocked.

## Implication

`MAX_CONCURRENT_BUILDS` is a module-level constant in
`src/main.py`; change it there if the concurrency limit needs
adjusting. Do not bypass the semaphore for new build paths. The
semaphore is module-level and not injected — tests that need a
lower limit must account for this.
