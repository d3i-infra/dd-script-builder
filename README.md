# dd-script-builder

FastAPI service that builds a data-donation task package. Copies a local `data-donation-task` repo, injects a per-platform config, runs `pnpm run release`, and serves the resulting zip.

## Setup

```bash
just install
```

Create a `.env` with:

```
TASK_SOURCE=/path/to/data-donation-task
```

`pnpm` must be on `PATH`. The process exits on startup if `TASK_SOURCE` is unset.

## Running

```bash
just dev      # hot-reload
just serve    # 0.0.0.0:8000
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/config?platform=<p>` | Generate config JSON for a platform |
| `POST` | `/build` | Queue a build |
| `GET` | `/builds` | List all builds |
| `GET` | `/status/{id}` | Build status and logs |
| `GET` | `/download/{id}` | Download zip (when `status == done`) |
| `DELETE` | `/build/{id}` | Delete build and temp files |

### POST /build

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `platform` | string | required | e.g. `"instagram"` — sets config path and `VITE_PLATFORM` |
| `config` | string | required | JSON written to `packages/python/port/configs/<platform>_config.json` |
| `documentation` | string | required | Written to `documentation.txt` in the zip |
| `output_dir` | string | `"releases"` | Subdir to zip |

Build states: `queued` → `running` → `done` \| `error`. Temp dirs are not cleaned up automatically — always call `DELETE` when done.

## just commands

```bash
just config <platform>    # fetch config JSON
just build <platform>     # trigger a build
just builds               # list builds
just status <build-id>    # get status
just watch <build-id>     # poll every 2s
just download <build-id>  # download zip
just delete <build-id>    # cleanup
just test / just test-v   # run tests
```
