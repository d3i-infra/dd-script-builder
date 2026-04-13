# dd-script-builder main.py Overhaul Design

**Date:** 2026-04-13  
**Scope:** Full rewrite of `src/main.py` — structured single-file, no new files added.

---

## Context

This service is called by a configurator (one directory up) to trigger builds of the `data-donation-task` repo. The build process copies a local repo, runs `pnpm install` + `pnpm build`, zips the output, and makes it available for download. The configurator downloads the zip and sends it to the end user.

---

## Goals

- Fix all correctness issues in the current code (hardcoded path not extracted, `inject_code` never called, `repo_url` field unused, logs not captured)
- Replace `threading.Semaphore` + `BackgroundTasks` pattern with proper `asyncio.Semaphore` + `asyncio.to_thread`
- Introduce a `BuildStore` class to make state swappable (in-memory now, Redis/SQLite later without API changes)
- Accumulate per-build logs so `GET /status` returns full log history
- Add `GET /builds` endpoint for listing all builds
- Remove dead code (`inject_code`, `repo_url`, `config` on request model)

---

## Architecture

Single file `src/main.py` with four logical sections:

### 1. BuildStore
Wraps `dict[str, dict]` with typed methods. All state access goes through this class.

```
BuildStore
  .create(build_id, initial_state)
  .update(build_id, **fields)
  .get(build_id) -> dict | None
  .delete(build_id)
  .all() -> dict
```

Swapping to Redis/SQLite means replacing only this class.

### 2. Constants
```python
REPO_SOURCE = "/home/turbo/d3i/dd-script-selector/data-donation-task"
MAX_CONCURRENT_BUILDS = 5
SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_BUILDS)
```

### 3. Build Worker
`run_build(build_id, req)` — runs as a background task via `asyncio.to_thread`.

Steps:
1. Acquire `SEMAPHORE`
2. `BuildStore.update(status="running")`
3. `cp -r REPO_SOURCE tmp_dir`
4. `pnpm install` (cwd=tmp_dir)
5. `pnpm build` (cwd=tmp_dir)
6. Locate `output_dir`, zip it
7. `BuildStore.update(status="done", file=archive_path, tmp_dir=tmp_dir)`
8. On exception: `BuildStore.update(status="error", error=str(e), tmp_dir=tmp_dir)`

Each step appends log lines to the build's `logs` list via `BuildStore.update`.

### 4. API Routes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/build` | Queue a new build, return `build_id` |
| GET | `/status/{build_id}` | Return status + logs |
| GET | `/download/{build_id}` | Stream zip (only if status=done) |
| DELETE | `/build/{build_id}` | Cleanup tmp_dir, remove from store |
| GET | `/builds` | List all builds |

---

## Request Model

```python
class BuildRequest(BaseModel):
    branch: str = "master"       # reserved for future use
    output_dir: str = "releases" # subdir of build output to zip
```

`repo_url` and `config` removed — repo is hardcoded, injection deferred.

---

## Response Shapes

```python
# POST /build
{ "build_id": "uuid" }

# GET /status/{build_id}
{ "status": "queued|running|done|error", "logs": ["..."], "error": "..." }

# GET /builds
{ "uuid": { "status": "...", "logs": [...] }, ... }

# DELETE /build/{build_id}
{ "status": "deleted" }

# GET /download/{build_id}
FileResponse(zip, filename="build.zip", media_type="application/zip")
```

---

## Data Flow

```
POST /build
  → BuildStore.create(id, status="queued", logs=[])
  → FastAPI BackgroundTask → asyncio.to_thread(run_build, id, req)
      → asyncio.Semaphore (max 5 concurrent)
      → BuildStore.update(status="running")
      → cp -r REPO_SOURCE → tmp_dir
      → pnpm install
      → pnpm build
      → zip output_dir → output.zip
      → BuildStore.update(status="done", file=path, tmp_dir=path)
      → on error: BuildStore.update(status="error", error=msg, tmp_dir=path)
      → each step: logs.append(msg)

GET /status/{id}  →  { status, logs }
GET /download/{id}  →  FileResponse(zip)
DELETE /build/{id}  →  rmtree(tmp_dir) + BuildStore.delete(id)
GET /builds  →  BuildStore.all()
```

---

## Error Handling

- Subprocess failure: captured in `run_cmd`, re-raised, caught in `run_build`, stored as `status="error"` with full stderr
- `tmp_dir` preserved on error so `DELETE` can still clean up
- 404 on unknown `build_id` for all endpoints
- 400 on download if status != "done"

---

## Out of Scope (deferred)

- Config injection (`inject_code`) — kept as a stub comment
- Docker-based builds
- Persistent state (Redis/SQLite)
- SSE/WebSocket log streaming
- `repo_url` / multi-repo support
