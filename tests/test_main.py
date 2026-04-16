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


MINIMAL_BUILD_REQ = {"config": "export default {}", "documentation": {}}


def test_post_build_returns_build_id():
    with patch("src.main.run_build", new=AsyncMock()):
        resp = client.post("/build", json=MINIMAL_BUILD_REQ)
    assert resp.status_code == 200
    assert "build_id" in resp.json()


def test_post_build_queues_status():
    with patch("src.main.run_build", new=AsyncMock()):
        resp = client.post("/build", json=MINIMAL_BUILD_REQ)
    build_id = resp.json()["build_id"]
    status_resp = client.get(f"/status/{build_id}")
    assert status_resp.json()["status"] == "queued"


def test_post_build_missing_config_returns_422():
    resp = client.post("/build", json={})
    assert resp.status_code == 422



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
