# CLAUDE.md

## Project overview

`dd-script-builder` is a FastAPI service that builds data-donation task packages. It clones a source repo into a temp dir, injects a JSON config, runs `pnpm run release`, and serves the output as a downloadable zip.

All logic lives in `src/main.py`. Tests are in `tests/test_main.py`.

## Dev commands

Use `just` — run `just` with no arguments to list all commands.

```bash
just install          # create .venv and install dependencies
just dev              # run dev server with hot-reload
just serve            # run server (production-like, binds 0.0.0.0:8000)
just test             # run tests
just test-v           # run tests verbosely

# API helpers (server must be running)
just config <platform>        # fetch generated config JSON
just build <platform>         # trigger a build
just builds                   # list all builds
just status <build-id>        # get build status
just watch <build-id>         # poll status every 2s
just download <build-id>      # download zip artifact
just delete <build-id>        # cleanup a build
```

`just` reads a `.env` file automatically (`set dotenv-load`), so put `TASK_SOURCE=...` there.

## Key constants in src/main.py

| Constant | Value | Purpose |
|----------|-------|---------|
| `TASK_SOURCE` | required env var | Source repo to copy for each build — process exits with `RuntimeError` if unset |
| `CONFIGS_DIR` | `packages/python/port/configs` | Directory inside the build dir where per-platform configs are injected |
| `MAX_CONCURRENT_BUILDS` | `5` | Max parallel builds (asyncio semaphore) |

Config is injected at `CONFIGS_DIR/<platform>_config.json` (computed by `config_path(platform)`). `VITE_PLATFORM` is set in the environment when running `pnpm run release` so only the requested platform is built. If the repo layout changes, update `CONFIGS_DIR` in `src/main.py` directly.

## Architecture

- **`BuildStore`** — in-memory dict keyed by UUID build ID. Holds status, logs, tmp_dir, and file path. Not persisted across restarts.
- **`run_build`** — async worker that runs under a semaphore. Copies repo, injects config, runs pnpm, zips output. Updates the store at each step.
- **Routes** — thin: create queues a background task, status/download/delete read or clean up store entries.

Build states: `queued` → `running` → `done` | `error`

## Notes

- Temp dirs are created per build with `tempfile.mkdtemp`. They are only cleaned up when the client calls `DELETE /build/{id}`. Forgotten builds leak disk space.
- Path traversal in `output_dir` is guarded with a `realpath` check.
- The build git commit hash from `TASK_SOURCE` is included in `documentation.txt` automatically.
- `format_doc_value` recursively formats nested dicts/lists into a readable text format for the documentation file.
