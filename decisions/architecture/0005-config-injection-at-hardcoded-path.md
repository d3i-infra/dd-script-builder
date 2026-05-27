# ADR 0005 — Config injection at per-platform path inside build dir

**Status:** Accepted. Source: conversation.

## Decision

After copying `TASK_SOURCE` into a temp dir, the service writes
the caller-supplied `config` string to a per-platform path derived
from the required `platform` field on `BuildRequest`:

```
packages/python/port/configs/<platform>_config.json
```

The directory (`CONFIGS_DIR`) is a module-level constant. The full
path is computed by `config_path(platform)` — it is not a request
parameter. Callers supply content and a platform name, not a path.

`pnpm run release` is invoked with `VITE_PLATFORM=<platform>` in
the environment so `release.sh` builds only that one platform.

## Background

The upstream data-donation-task moved from a single
`port/port_config.json` to per-platform files in `port/configs/`
(data-donation-task fork-governance/AD0005 amendment 2026-05-20,
python-architecture/AD0012–14). `release.sh` now discovers
platforms by globbing `configs/*_config.json` and requires
`VITE_PLATFORM` to be set for single-platform builds.

## Implication

If the source repo layout changes, update `CONFIGS_DIR` in
`src/main.py` directly. Do not expose the path as an API
parameter — callers supply content, not location.
