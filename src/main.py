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
