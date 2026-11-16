"""Tests — Metaclasses & Class Factories"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from advanced_concepts.oop.metaclass import (
    PluginMeta, CSVPlugin, JSONPlugin, XMLPlugin,
    Command, StartCommand, StopCommand, ReloadCommand,
    StrictMeta, _handlers,
)


# ── PluginMeta registry ───────────────────────────────────────────────────

def test_csv_plugin_registered():
    assert PluginMeta.get("csvplugin") is CSVPlugin


def test_json_plugin_registered():
    assert PluginMeta.get("jsonplugin") is JSONPlugin


def test_xml_plugin_registered():
    assert PluginMeta.get("xmlplugin") is XMLPlugin


def test_plugin_lookup_case_insensitive():
    assert PluginMeta.get("CSVPlugin") is CSVPlugin


def test_unknown_plugin_raises():
    with pytest.raises(KeyError):
        PluginMeta.get("unknown")


def test_plugin_run():
    assert "CSV" in CSVPlugin().run()
    assert "JSON" in JSONPlugin().run()
    assert "XML" in XMLPlugin().run()


# ── __init_subclass__ command registry ────────────────────────────────────

def test_start_command_registered():
    assert Command._registry.get("start") is StartCommand


def test_stop_command_registered():
    assert Command._registry.get("stop") is StopCommand


def test_reload_command_registered():
    assert Command._registry.get("reload") is ReloadCommand


def test_command_execute():
    assert "start" in StartCommand().execute().lower()
    assert "stop"  in StopCommand().execute().lower()


# ── Class decorator event handler registry ────────────────────────────────

def test_user_created_handler_registered():
    assert "user.created" in _handlers


def test_order_placed_handler_registered():
    assert "order.placed" in _handlers


def test_handler_handle():
    result = _handlers["user.created"]().handle({"email": "a@b.com"})
    assert "a@b.com" in result

    result = _handlers["order.placed"]().handle({"id": "ORD-1"})
    assert "ORD-1" in result


# ── Validation metaclass ──────────────────────────────────────────────────

def test_missing_docstring_raises_at_definition():
    class Base(metaclass=StrictMeta):
        """Base is fine."""

    with pytest.raises(TypeError, match="docstring"):
        class Child(Base):
            pass   # no docstring — StrictMeta sees bases=[Base] and raises


def test_valid_class_passes():
    class GoodSvc(metaclass=StrictMeta):
        """A well-formed service."""
        def process(self) -> str:
            return "ok"

    assert GoodSvc().process() == "ok"
