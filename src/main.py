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
