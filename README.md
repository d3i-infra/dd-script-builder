# dd-script-builder

FastAPI service that builds a data-donation task package and returns a zip artifact.

It copies a source repo (`data-donation-task`), injects a config file, runs `pnpm run release`, and serves the resulting zip for download.

## Setup

```bash
pip install -r requirements.txt
```

Requires `pnpm` to be available on `PATH` (used during the build step).

The `REPO_SOURCE` environment variable must be set to the path of the `data-donation-task` repo. The process will exit on startup if it is not set.

## Start

```bash
REPO_SOURCE=/path/to/data-donation-task python3 -m uvicorn src.main:app --reload
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/build` | Queue a new build |
| `GET` | `/builds` | List all builds |
| `GET` | `/status/{build_id}` | Get build status and logs |
| `GET` | `/download/{build_id}` | Download zip artifact (when `status == done`) |
| `DELETE` | `/build/{build_id}` | Delete build and clean up temp files |

### POST /build

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `config` | string | required | Contents written to the config file in the build |
| `documentation` | object | required | Key/value pairs written to `documentation.txt` in the zip |
| `output_dir` | string | `"releases"` | Subdir of the build output to zip |

The config is injected at the hardcoded path `packages/python/port/port_config.json` inside the build directory.

### Build lifecycle

A build moves through these states: `queued` → `running` → `done` or `error`.

Poll `/status/{build_id}` to track progress. The `logs` field contains step-by-step output. Download the artifact once `status == done`. Call `DELETE` when done to clean up temp files.

### Examples

```bash
# Start a build
curl -s -X POST http://localhost:8000/build \
  -H "Content-Type: application/json" \
  -d '{"config": "{\"platform\": \"instagram\"}", "documentation": {"platform": "instagram"}}'

# Check status
curl -s http://localhost:8000/status/<build-id>

# Poll until done
watch -n 2 "curl -s http://localhost:8000/status/<build-id>"

# Download zip
curl -O -J http://localhost:8000/download/<build-id>

# Cleanup
curl -s -X DELETE http://localhost:8000/build/<build-id>
```

See `cmds.txt` for more examples.

## Tests

```bash
pytest
```
