from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import tempfile
import os
import uuid
import shutil
import threading
import json

app = FastAPI()

# In-memory store (replace with Redis/db in production)
BUILDS: dict[str, dict] = {}

# Limit concurrent builds
SEMAPHORE = threading.Semaphore(5)


# ----------------------------
# Request model
# ----------------------------

class BuildRequest(BaseModel):
    repo_url: str
    branch: str | None = "master"
    config: dict | None = None
    output_dir: str | None = "releases"


# ----------------------------
# Helpers
# ----------------------------

def run_cmd(cmd, cwd=None):
    print(f"[cmd] Running: {' '.join(cmd)}", flush=True)
    if cwd:
        print(f"[cmd] CWD: {cwd}", flush=True)

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(f"[cmd stdout]\n{result.stdout}", flush=True)

    if result.stderr:
        print(f"[cmd stderr]\n{result.stderr}", flush=True)

    if result.returncode != 0:
        print(f"[cmd error] Command failed with exit code {result.returncode}", flush=True)
        raise Exception(
            f"Command failed: {' '.join(cmd)}\n"
            f"Exit code: {result.returncode}\n"
            f"stderr:\n{result.stderr}"
        )

    return result.stdout


def inject_code(config: dict | None, repo_dir: str):
    if not config:
        return

    path = os.path.join(repo_dir, "build.config.json")
    with open(path, "w") as f:
        json.dump(config, f)


def zip_output(output_dir: str, tmp_dir: str):
    return shutil.make_archive(
        base_name=os.path.join(tmp_dir, "output"),
        format="zip",
        root_dir=output_dir
    )


# ----------------------------
# Build worker
# ----------------------------

def run_build(build_id: str, req: BuildRequest):
    import time

    def log(msg):
        print(f"[build={build_id}] {msg}", flush=True)

    with SEMAPHORE:
        tmp_dir = tempfile.mkdtemp(prefix="build_")

        log("Build started")
        log(f"Temp dir: {tmp_dir}")
        log(f"Repo: {req.repo_url}")
        log(f"Branch: {req.branch}")
        log(f"Output dir: {req.output_dir}")

        BUILDS[build_id] = {
            "status": "running",
            "log": ""
        }

        try:
            # Step 1: Copy repo
            log("Copying repo")

            run_cmd([
                "cp",
                "-r",
                "/home/turbo/d3i/dd-script-selector/data-donation-task/.",
                tmp_dir
            ])

            log("Repo copied")

            # Step 2: Install dependencies
            log("Running pnpm install")
            run_cmd(["pnpm", "install"], cwd=tmp_dir)
            log("pnpm install complete")

            # Step 3: Build
            log("Running pnpm build")
            run_cmd(["pnpm", "build"], cwd=tmp_dir)
            log("pnpm build complete")

            # Step 4: Locate output
            output_path = os.path.join(tmp_dir, req.output_dir)
            log(f"Checking output path: {output_path}")

            if not os.path.exists(output_path):
                log("Output directory missing")
                raise Exception(f"Output directory '{req.output_dir}' not found")

            # Step 5: Zip output
            log("Creating zip archive")
            archive_path = zip_output(output_path, tmp_dir)

            log(f"Zip created at: {archive_path}")

            BUILDS[build_id] = {
                "status": "done",
                "file": archive_path,
                "tmp_dir": tmp_dir
            }

            log("Build completed successfully")

        except Exception as e:
            log(f"ERROR: {str(e)}")

            BUILDS[build_id] = {
                "status": "error",
                "error": str(e),
                "tmp_dir": tmp_dir
            }

        finally:
            log("Build process finished")

# ----------------------------
# API endpoints
# ----------------------------

@app.post("/build")
def create_build(req: BuildRequest, bg: BackgroundTasks):
    build_id = str(uuid.uuid4())

    BUILDS[build_id] = {
        "status": "queued"
    }

    bg.add_task(run_build, build_id, req)

    return {
        "build_id": build_id
    }


@app.get("/status/{build_id}")
def get_status(build_id: str):
    result = BUILDS.get(build_id)

    if not result:
        raise HTTPException(404, "Build not found")

    return result


@app.get("/download/{build_id}")
def download(build_id: str):
    result = BUILDS.get(build_id)

    if not result:
        raise HTTPException(404, "Build not found")

    if result["status"] != "done":
        raise HTTPException(400, "Build not finished")

    return FileResponse(
        result["file"],
        filename="build.zip",
        media_type="application/zip"
    )


@app.delete("/build/{build_id}")
def cleanup(build_id: str):
    result = BUILDS.get(build_id)

    if not result:
        raise HTTPException(404, "Build not found")

    tmp_dir = result.get("tmp_dir")

    if tmp_dir and os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    del BUILDS[build_id]

    return {"status": "deleted"}
