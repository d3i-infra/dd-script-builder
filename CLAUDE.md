# CLAUDE.md

## Project overview

`dd-script-builder` is a FastAPI service that builds data-donation task packages. It clones a source repo into a temp dir, injects a JSON config, runs `pnpm run release`, and serves the output as a downloadable zip.

All logic lives in `src/main.py`. Tests are in `tests/test_main.py`.

## Dev commands

```bash
# Run the server
python3 -m uvicorn src.main:app --reload

# Run tests
pytest

# Get a platform config (server must be running)
curl "http://localhost:8000/config?platform=<platform_name>"
```

## Key constants in src/main.py

| Constant | Value | Purpose |
|----------|-------|---------|
| `REPO_SOURCE` | required env var | Source repo to copy for each build — process exits with `RuntimeError` if unset |
| `CONFIG_PATH` | `packages/python/port/port_config.json` | Path inside the build dir where config is injected |
| `MAX_CONCURRENT_BUILDS` | `5` | Max parallel builds (asyncio semaphore) |

Both `REPO_SOURCE` and `CONFIG_PATH` are hardcoded — change them directly in `src/main.py` if the repo layout changes.

## Architecture

- **`BuildStore`** — in-memory dict keyed by UUID build ID. Holds status, logs, tmp_dir, and file path. Not persisted across restarts.
- **`run_build`** — async worker that runs under a semaphore. Copies repo, injects config, runs pnpm, zips output. Updates the store at each step.
- **Routes** — thin: create queues a background task, status/download/delete read or clean up store entries.

Build states: `queued` → `running` → `done` | `error`

## Notes

- Temp dirs are created per build with `tempfile.mkdtemp`. They are only cleaned up when the client calls `DELETE /build/{id}`. Forgotten builds leak disk space.
- Path traversal in `output_dir` is guarded with a `realpath` check.
- The build git commit hash from `REPO_SOURCE` is included in `documentation.txt` automatically.
- `format_doc_value` recursively formats nested dicts/lists into a readable text format for the documentation file.
