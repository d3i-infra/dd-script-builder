# Architectural decisions

This directory holds the project's Architectural Decision
Records (ADRs). The framework and conventions are defined in
[`0001-adr-framework-and-conventions.md`](./0001-adr-framework-and-conventions.md);
read it first.

## Index

### Meta

- [0001 — ADR framework and conventions](./0001-adr-framework-and-conventions.md)

### Application shape

- [0002 — FastAPI as the web framework](./0002-fastapi-as-web-framework.md)
- [0003 — In-memory build store, no persistence](./0003-in-memory-build-store-no-persistence.md)
- [0004 — Async semaphore-bounded build execution](./0004-async-semaphore-bounded-build-execution.md)
- [0006 — TASK_SOURCE required env var; fail fast on startup](./0006-task-source-required-env-var-fail-fast.md)

### Build pipeline

- [0005 — Config injection at per-platform path inside build dir](./0005-config-injection-at-hardcoded-path.md)
- [0009 — Provenance documentation written into every artifact](./0009-provenance-documentation-in-artifact.md)
- [0010 — pnpm as the JS build tool](./0010-pnpm-as-build-tool.md)

### Resource management

- [0007 — Client-managed temp dir cleanup](./0007-client-managed-temp-dir-cleanup.md)

### Security

- [0008 — Path traversal guard on output_dir](./0008-path-traversal-guard-on-output-dir.md)

## How to use this directory

When working on code in this repo, load the ADR(s) whose
filenames match the area you are touching. Before adding a new
route, read 0002. Before changing build flow, read 0004 and 0005.
Before touching cleanup, read 0007. Before any path handling,
read 0008.

When a decision surfaces in conversation that warrants an ADR
but does not yet have one, prompt the user to escalate. Do not
silently encode a decision into code without an ADR to back it.
