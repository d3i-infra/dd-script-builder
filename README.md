# dd-script-builder

FastAPI service that builds a data-donation task package and returns a zip artifact.

## Start

```
python3 -m uvicorn src.main:app --reload
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/build` | Queue a new build |
| `GET` | `/builds` | List all builds |
| `GET` | `/status/{build_id}` | Get build status and logs |
| `GET` | `/download/{build_id}` | Download zip artifact (when `status == done`) |
| `DELETE` | `/build/{build_id}` | Delete build and clean up temp files |

### POST /build — required fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `config` | string | — | Config file contents to inject |
| `config_path` | string | — | Path (relative to build dir) where config is written |
| `documentation` | object | — | Key/value pairs written to `documentation.txt` in the zip |
| `output_dir` | string | `"releases"` | Subdir of the build output to zip |

### Example

```bash
curl -s -X POST http://localhost:8000/build \
  -H "Content-Type: application/json" \
  -d '{"config": "{\"platform\": \"instagram\"}", "config_path": "port_config.json", "documentation": {"platform": "instagram"}}'
```

See `cmds.txt` for more examples.

## Tests

```
pytest
```
