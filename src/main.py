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
