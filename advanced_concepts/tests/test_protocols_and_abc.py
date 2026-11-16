"""Tests — Protocols vs ABC"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from advanced_concepts.oop.protocols_and_abc import (
    JSONExporter, CSVExporter, BrokenExporter,
    Serializable, Invoice, LogEntry, MemoryBackend,
)


# ── ABC ───────────────────────────────────────────────────────────────────

def test_json_exporter_content_type():
    assert JSONExporter().content_type == "application/json"


def test_csv_exporter_content_type():
    assert CSVExporter().content_type == "text/csv"


def test_json_exporter_output():
    result = JSONExporter().export({"id": 1, "name": "Alice"})
    import json
    data = json.loads(result)
    assert data["name"] == "Alice"


def test_csv_exporter_output():
    result = CSVExporter().export({"id": 1, "name": "Alice"})
    lines = result.splitlines()
    assert lines[0] == "id,name"
    assert lines[1] == "1,Alice"


def test_broken_exporter_raises_on_instantiation():
    with pytest.raises(TypeError):
        BrokenExporter()


# ── Protocol ─────────────────────────────────────────────────────────────

def test_invoice_is_serializable():
    assert isinstance(Invoice("INV-001", 100.0), Serializable)


def test_log_entry_is_serializable():
    assert isinstance(LogEntry("boot"), Serializable)


def test_invoice_serialize_output():
    result = Invoice("INV-001", 250.0).serialize()
    assert "INV-001" in result
    assert "250.0" in result


def test_log_entry_serialize_output():
    result = LogEntry("server started").serialize()
    assert "server started" in result


def test_non_serializable_object_fails_isinstance():
    class NoSerialize:
        pass
    assert not isinstance(NoSerialize(), Serializable)


# ── Storage backend ───────────────────────────────────────────────────────

def test_memory_backend_write_read():
    b = MemoryBackend()
    b.write("key", b"value")
    assert b.read("key") == b"value"


def test_memory_backend_overwrite():
    b = MemoryBackend()
    b.write("k", b"v1")
    b.write("k", b"v2")
    assert b.read("k") == b"v2"
