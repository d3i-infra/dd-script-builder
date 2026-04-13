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
