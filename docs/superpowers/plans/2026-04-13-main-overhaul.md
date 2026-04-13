# main.py Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `src/main.py` as a clean, structured FastAPI build server with a swappable `BuildStore`, proper async via `asyncio.to_thread`, per-build log accumulation, and all dead code removed.

**Architecture:** Single-file rewrite of `src/main.py` in four sections: `BuildStore` class, helper functions (`run_cmd`, `zip_output`), async `run_build` worker, and API routes. State is in-memory via `BuildStore` but fully encapsulated for easy future swap to Redis/SQLite.

**Tech Stack:** Python 3.14, FastAPI, Pydantic, asyncio, pytest, httpx

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/main.py` | Rewrite | Full application — BuildStore, helpers, worker, routes |
| `tests/__init__.py` | Create | Makes tests a package |
| `tests/test_main.py` | Create | All tests |

---

### Task 1: Install test dependencies

**Files:**
- Run: `.venv` pip installs

- [ ] **Step 1: Install pytest and httpx**

```bash
.venv/bin/pip install pytest httpx
```

Expected output includes: `Successfully installed pytest-... httpx-...`

- [ ] **Step 2: Verify pytest runs**

```bash
.venv/bin/python -m pytest --version
```

Expected: `pytest 8.x.x`

- [ ] **Step 3: Create test scaffold**

Create `tests/__init__.py` (empty file) and `tests/test_main.py`:

```python
# tests/test_main.py
# Tests added task by task
```

- [ ] **Step 4: Confirm pytest discovers the file**

```bash
.venv/bin/python -m pytest tests/ --collect-only
```

Expected: `0 tests collected` with no errors.

---

### Task 2: BuildStore — test then implement

**Files:**
- Modify: `src/main.py` (add BuildStore class)
- Modify: `tests/test_main.py`

- [ ] **Step 1: Write failing tests for BuildStore**

Replace `tests/test_main.py` with:

```python
import pytest
from src.main import BuildStore


def test_create_and_get():
    s = BuildStore()
    s.create("id1", {"status": "queued", "logs": []})
    assert s.get("id1") == {"status": "queued", "logs": []}


def test_get_unknown_returns_none():
    s = BuildStore()
    assert s.get("nope") is None


def test_update_merges_fields():
    s = BuildStore()
    s.create("id1", {"status": "queued", "logs": []})
    s.update("id1", status="running")
    result = s.get("id1")
    assert result["status"] == "running"
    assert result["logs"] == []


def test_update_unknown_is_noop():
    s = BuildStore()
    s.update("nope", status="running")  # should not raise


def test_delete_removes_entry():
    s = BuildStore()
    s.create("id1", {"status": "queued"})
    s.delete("id1")
    assert s.get("id1") is None


def test_delete_unknown_is_noop():
    s = BuildStore()
    s.delete("nope")  # should not raise


def test_all_returns_snapshot():
    s = BuildStore()
    s.create("id1", {"status": "queued"})
    s.create("id2", {"status": "running"})
    result = s.all()
    assert "id1" in result
    assert "id2" in result
    # Mutating the snapshot should not affect the store
    result["id3"] = {}
    assert s.get("id3") is None
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
.venv/bin/python -m pytest tests/test_main.py -v
```

Expected: `ImportError: cannot import name 'BuildStore' from 'src.main'`

- [ ] **Step 3: Add BuildStore to src/main.py**

Replace all of `src/main.py` with:

```python
import asyncio
import os
import shutil
import subprocess
import tempfile
import uuid
from typing import Callable

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ----------------------------
# Constants
# ----------------------------

REPO_SOURCE = "/home/turbo/d3i/dd-script-selector/data-donation-task"
MAX_CONCURRENT_BUILDS = 5
SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_BUILDS)

app = FastAPI()


# ----------------------------
# BuildStore
# ----------------------------

class BuildStore:
    def __init__(self):
        self._store: dict[str, dict] = {}

    def create(self, build_id: str, state: dict) -> None:
        self._store[build_id] = state

    def get(self, build_id: str) -> dict | None:
        return self._store.get(build_id)

    def update(self, build_id: str, **fields) -> None:
        if build_id in self._store:
            self._store[build_id].update(fields)

    def delete(self, build_id: str) -> None:
        self._store.pop(build_id, None)

    def all(self) -> dict:
        return dict(self._store)


store = BuildStore()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
.venv/bin/python -m pytest tests/test_main.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add src/main.py tests/__init__.py tests/test_main.py
git commit -m "feat: add BuildStore with full test coverage"
```

---

### Task 3: run_cmd helper — test then implement

**Files:**
- Modify: `src/main.py` (add run_cmd)
- Modify: `tests/test_main.py`

- [ ] **Step 1: Add failing tests for run_cmd**

Append to `tests/test_main.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from src.main import run_cmd


def test_run_cmd_returns_stdout():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="hello\n", stderr="")
        result = run_cmd(["echo", "hello"])
        assert result == "hello\n"


def test_run_cmd_failure_raises_runtime_error():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="bad thing")
        with pytest.raises(RuntimeError, match="Command failed"):
            run_cmd(["false"])


def test_run_cmd_calls_log_with_command():
    logged = []
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_cmd(["echo", "hi"], log=logged.append)
        assert any("echo" in entry for entry in logged)


def test_run_cmd_passes_cwd():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_cmd(["ls"], cwd="/tmp")
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs["cwd"] == "/tmp"
```

- [ ] **Step 2: Run tests — verify new ones fail**

```bash
.venv/bin/python -m pytest tests/test_main.py -v -k "run_cmd"
```

Expected: `ImportError` or `4 failed`

- [ ] **Step 3: Add run_cmd to src/main.py**

Append after the `store = BuildStore()` line:

```python

# ----------------------------
# Helpers
# ----------------------------

def run_cmd(
    cmd: list[str],
    cwd: str | None = None,
    log: Callable[[str], None] = print,
) -> str:
    log(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        log(result.stdout.strip())
    if result.stderr:
        log(result.stderr.strip())
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n"
            f"Exit code: {result.returncode}\n"
            f"stderr: {result.stderr}"
        )
    return result.stdout


def zip_output(output_dir: str, tmp_dir: str) -> str:
    return shutil.make_archive(
        base_name=os.path.join(tmp_dir, "output"),
        format="zip",
        root_dir=output_dir,
    )
```

- [ ] **Step 4: Run all tests — verify they pass**

```bash
.venv/bin/python -m pytest tests/test_main.py -v
```

Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: add run_cmd and zip_output helpers with tests"
```

---

### Task 4: zip_output helper — test then implement

> `zip_output` was already added in Task 3. This task adds its tests.

**Files:**
- Modify: `tests/test_main.py`

- [ ] **Step 1: Add failing test for zip_output**

Append to `tests/test_main.py`:

```python
import os
import tempfile
import zipfile
from src.main import zip_output


def test_zip_output_creates_archive():
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = os.path.join(tmp, "releases")
        os.makedirs(output_dir)
        with open(os.path.join(output_dir, "bundle.js"), "w") as f:
            f.write("console.log('hi')")

        archive = zip_output(output_dir, tmp)

        assert os.path.exists(archive)
        assert archive.endswith(".zip")
        with zipfile.ZipFile(archive) as zf:
            assert "bundle.js" in zf.namelist()
```

- [ ] **Step 2: Run test — verify it passes immediately (implementation already exists)**

```bash
.venv/bin/python -m pytest tests/test_main.py::test_zip_output_creates_archive -v
```

Expected: `1 passed`

- [ ] **Step 3: Commit**

```bash
git add tests/test_main.py
git commit -m "test: add zip_output test"
```

---

### Task 5: API routes — full main.py completion + route tests

**Files:**
- Modify: `src/main.py` (add BuildRequest, run_build, all routes)
- Modify: `tests/test_main.py`

- [ ] **Step 1: Add failing route tests**

Append to `tests/test_main.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app, store


@pytest.fixture(autouse=True)
def clear_store():
    store._store.clear()
    yield
    store._store.clear()


client = TestClient(app)


def test_post_build_returns_build_id():
    with patch("src.main.run_build", new=AsyncMock()):
        resp = client.post("/build", json={})
    assert resp.status_code == 200
    assert "build_id" in resp.json()


def test_post_build_queues_status():
    with patch("src.main.run_build", new=AsyncMock()):
        resp = client.post("/build", json={})
    build_id = resp.json()["build_id"]
    status_resp = client.get(f"/status/{build_id}")
    assert status_resp.json()["status"] == "queued"


def test_get_status_unknown_returns_404():
    resp = client.get("/status/does-not-exist")
    assert resp.status_code == 404


def test_get_status_includes_logs():
    store.create("test-id", {"status": "running", "logs": ["step 1", "step 2"]})
    resp = client.get("/status/test-id")
    assert resp.status_code == 200
    assert resp.json()["logs"] == ["step 1", "step 2"]


def test_download_unknown_returns_404():
    resp = client.get("/download/does-not-exist")
    assert resp.status_code == 404


def test_download_not_done_returns_400():
    store.create("test-id", {"status": "running", "logs": []})
    resp = client.get("/download/test-id")
    assert resp.status_code == 400


def test_download_done_returns_zip():
    with tempfile.TemporaryDirectory() as tmp:
        # create a real zip file
        output_dir = os.path.join(tmp, "releases")
        os.makedirs(output_dir)
        with open(os.path.join(output_dir, "file.js"), "w") as f:
            f.write("x")
        archive = zip_output(output_dir, tmp)
        store.create("test-id", {"status": "done", "file": archive, "tmp_dir": tmp, "logs": []})
        resp = client.get("/download/test-id")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"


def test_delete_unknown_returns_404():
    resp = client.delete("/build/does-not-exist")
    assert resp.status_code == 404


def test_delete_removes_from_store_and_cleans_tmp():
    with tempfile.TemporaryDirectory() as tmp:
        store.create("test-id", {"status": "done", "tmp_dir": tmp, "logs": []})
        resp = client.delete("/build/test-id")
        assert resp.status_code == 200
        assert resp.json() == {"status": "deleted"}
        assert store.get("test-id") is None


def test_list_builds_returns_all():
    store.create("id1", {"status": "queued", "logs": []})
    store.create("id2", {"status": "running", "logs": []})
    resp = client.get("/builds")
    assert resp.status_code == 200
    body = resp.json()
    assert "id1" in body
    assert "id2" in body
```

- [ ] **Step 2: Run new tests — verify they fail**

```bash
.venv/bin/python -m pytest tests/test_main.py -v -k "build or status or download or delete or list"
```

Expected: failures due to missing routes/model.

- [ ] **Step 3: Complete src/main.py — add BuildRequest, run_build, and all routes**

Append to the end of `src/main.py`:

```python

# ----------------------------
# Request model
# ----------------------------

class BuildRequest(BaseModel):
    branch: str = "master"        # reserved for future git support
    output_dir: str = "releases"  # subdir of build output to zip


# ----------------------------
# Build worker
# ----------------------------

async def run_build(build_id: str, req: BuildRequest) -> None:
    logs: list[str] = []

    def log(msg: str) -> None:
        print(f"[build={build_id}] {msg}", flush=True)
        logs.append(msg)
        store.update(build_id, logs=list(logs))

    async with SEMAPHORE:
        tmp_dir = tempfile.mkdtemp(prefix="build_")
        store.update(build_id, status="running", tmp_dir=tmp_dir)

        try:
            log("Build started")

            await asyncio.to_thread(
                run_cmd,
                ["cp", "-r", f"{REPO_SOURCE}/.", tmp_dir],
                log=log,
            )
            log("Repo copied")

            await asyncio.to_thread(run_cmd, ["pnpm", "install"], tmp_dir, log)
            log("pnpm install complete")

            await asyncio.to_thread(run_cmd, ["pnpm", "build"], tmp_dir, log)
            log("pnpm build complete")

            output_path = os.path.join(tmp_dir, req.output_dir)
            if not os.path.exists(output_path):
                raise RuntimeError(f"Output directory '{req.output_dir}' not found after build")

            archive_path = await asyncio.to_thread(zip_output, output_path, tmp_dir)
            log(f"Archive created: {archive_path}")

            store.update(build_id, status="done", file=archive_path)
            log("Build completed successfully")

        except Exception as e:
            log(f"ERROR: {e}")
            store.update(build_id, status="error", error=str(e))


# ----------------------------
# Routes
# ----------------------------

@app.post("/build")
def create_build(req: BuildRequest, bg: BackgroundTasks):
    build_id = str(uuid.uuid4())
    store.create(build_id, {"status": "queued", "logs": []})
    bg.add_task(run_build, build_id, req)
    return {"build_id": build_id}


@app.get("/builds")
def list_builds():
    return store.all()


@app.get("/status/{build_id}")
def get_status(build_id: str):
    result = store.get(build_id)
    if not result:
        raise HTTPException(404, "Build not found")
    return result


@app.get("/download/{build_id}")
def download(build_id: str):
    result = store.get(build_id)
    if not result:
        raise HTTPException(404, "Build not found")
    if result["status"] != "done":
        raise HTTPException(400, "Build not finished")
    return FileResponse(result["file"], filename="build.zip", media_type="application/zip")


@app.delete("/build/{build_id}")
def cleanup(build_id: str):
    result = store.get(build_id)
    if not result:
        raise HTTPException(404, "Build not found")
    tmp_dir = result.get("tmp_dir")
    if tmp_dir and os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    store.delete(build_id)
    return {"status": "deleted"}
```

- [ ] **Step 4: Run all tests — verify they all pass**

```bash
.venv/bin/python -m pytest tests/test_main.py -v
```

Expected: all tests pass (approximately 23 tests).

- [ ] **Step 5: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: complete main.py overhaul — BuildStore, async worker, full route coverage"
```

---

### Task 6: Smoke test the running server

**Files:**
- No changes

- [ ] **Step 1: Start the server**

```bash
.venv/bin/python -m uvicorn src.main:app --reload
```

Expected: `Uvicorn running on http://127.0.0.1:8000`

- [ ] **Step 2: Queue a build**

In a second terminal:

```bash
curl -s -X POST http://localhost:8000/build -H "Content-Type: application/json" -d '{}' | python3 -m json.tool
```

Expected:
```json
{
    "build_id": "<some-uuid>"
}
```

- [ ] **Step 3: Poll status**

```bash
curl -s http://localhost:8000/status/<build_id> | python3 -m json.tool
```

Expected: `status` is one of `queued`, `running`, `done`, or `error`. Logs array populated as build progresses.

- [ ] **Step 4: List builds**

```bash
curl -s http://localhost:8000/builds | python3 -m json.tool
```

Expected: JSON object with the build_id as a key.

- [ ] **Step 5: Download (once status=done)**

```bash
curl -o build.zip http://localhost:8000/download/<build_id>
file build.zip
```

Expected: `build.zip: Zip archive data`

- [ ] **Step 6: Clean up**

```bash
curl -s -X DELETE http://localhost:8000/build/<build_id> | python3 -m json.tool
```

Expected:
```json
{
    "status": "deleted"
}
```
