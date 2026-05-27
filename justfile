set dotenv-load

# List available commands
default:
    @just --list

# --- Dev ---

# Install Python dependencies into .venv
install:
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

# Check that .env exists and TASK_SOURCE is set
check-env:
    @test -f .env || (echo "Error: .env file not found.\nCreate a .env file with:\n  TASK_SOURCE=/path/to/data-donation-task" && exit 1)
    @test -n "${TASK_SOURCE:-}" || (echo "Error: TASK_SOURCE is not set in .env.\nAdd the following line to your .env file:\n  TASK_SOURCE=/path/to/data-donation-task" && exit 1)

# Run the dev server (hot-reload)
dev: check-env
    .venv/bin/python -m uvicorn src.main:app --reload

# Run the server without reload (production-like)
serve: check-env
    .venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Run tests
test:
    .venv/bin/pytest tests/

# Run tests with verbose output
test-v:
    .venv/bin/pytest tests/ -v

# --- API helpers (server must be running) ---

# Get the generated config for a platform  (usage: just config instagram)
config platform:
    curl -s "http://localhost:8000/config?platform={{platform}}" | python3 -m json.tool

# Trigger a build  (usage: just build instagram)
build platform:
    curl -s -X POST http://localhost:8000/build \
      -H "Content-Type: application/json" \
      --data "$(jq -n \
        --arg platform "{{platform}}" \
        --arg config "$(curl -s "http://localhost:8000/config?platform={{platform}}")" \
        --arg doc "build for {{platform}}" \
        '{platform: $platform, config: $config, documentation: $doc}')" \
      | python3 -m json.tool

# List all builds
builds:
    curl -s http://localhost:8000/builds | python3 -m json.tool

# Get status of a build  (usage: just status <build-id>)
status build_id:
    curl -s "http://localhost:8000/status/{{build_id}}" | python3 -m json.tool

# Poll build status every 2s until done  (usage: just watch <build-id>)
watch build_id:
    watch -n 2 "curl -s http://localhost:8000/status/{{build_id}} | python3 -m json.tool"

# Download the zip artifact  (usage: just download <build-id>)
download build_id:
    curl -O -J "http://localhost:8000/download/{{build_id}}"

# Delete / cleanup a build  (usage: just delete <build-id>)
delete build_id:
    curl -s -X DELETE "http://localhost:8000/build/{{build_id}}" | python3 -m json.tool
