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
