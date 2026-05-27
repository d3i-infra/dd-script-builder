# ADR 0010 — pnpm as the JS build tool

**Status:** Accepted. Source: conversation.

## Decision

The build step executes `pnpm run release` inside the copied repo.
Config generation uses `pnpm run --silent generate-config`.
`pnpm` must be available on `PATH` at runtime; the service does
not install it.

## Implication

Deployment environments must have `pnpm` installed. Do not
substitute `npm` or `yarn` without updating the source repo's
scripts and writing a new ADR.
