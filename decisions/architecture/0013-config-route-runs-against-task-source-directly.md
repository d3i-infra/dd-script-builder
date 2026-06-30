# ADR 0013 — /config route runs generate-config against TASK_SOURCE directly

**Status:** Accepted. Source: conversation.

## Decision

`GET /config?platform=<p>` runs `pnpm run --silent generate-config`
in `TASK_SOURCE` (the original checkout) rather than in a copied
temp dir. No copy is made; the route is a read-only probe.

## Implication

Config generation is cheap and stateless — it does not write files,
so running against the original is safe. Keep this route read-only:
if a future generate-config script writes side effects, it must be
run in a copy instead (and this ADR updated).
