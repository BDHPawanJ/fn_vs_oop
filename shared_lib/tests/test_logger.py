"""Tests — Logger: functional vs OOP produce same output, different state model."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import logging
import shared_lib.functional.logger as fn_log
from shared_lib.oop.logger import Logger


# ── Functional ────────────────────────────────────────────────────────────

def setup_function():
    fn_log._state.clear()


def test_fn_configure_sets_logger():
    fn_log.configure(name="test-fn", level="DEBUG")
    assert "logger" in fn_log._state
    assert fn_log._state["logger"].name == "test-fn"


def test_fn_configure_level():
    fn_log.configure(name="test-fn", level="WARNING")
    assert fn_log._state["logger"].level == logging.WARNING


def test_fn_bind_adds_to_global_state():
    fn_log.configure(name="test-fn", level="DEBUG")
    fn_log.bind(request_id="req-001", user="alice")
    assert fn_log._state["extra"]["request_id"] == "req-001"
    assert fn_log._state["extra"]["user"] == "alice"


def test_fn_bind_is_global_mutation():
    fn_log.configure(name="test-fn", level="DEBUG")
    fn_log.bind(env="prod")
    fn_log.bind(version="1.0")
    assert fn_log._state["extra"]["env"] == "prod"
    assert fn_log._state["extra"]["version"] == "1.0"


def test_fn_get_child_returns_stdlib_logger():
    fn_log.configure(name="test-fn", level="DEBUG")
    child = fn_log.get_child("db")
    assert isinstance(child, logging.Logger)
    assert child.name == "test-fn.db"


def test_fn_log_functions_do_not_raise():
    fn_log.configure(name="test-fn", level="DEBUG")
    fn_log.debug("debug msg")
    fn_log.info("info msg")
    fn_log.warning("warn msg")
    fn_log.error("error msg")


# ── OOP ───────────────────────────────────────────────────────────────────

def test_oop_singleton_same_instance():
    Logger.reset()
    a = Logger.get_instance(name="oop-test", level="DEBUG")
    b = Logger.get_instance()
    assert a is b


def test_oop_reset_creates_new_instance():
    Logger.reset()
    a = Logger.get_instance(name="oop-test")
    Logger.reset()
    b = Logger.get_instance(name="oop-test")
    assert a is not b


def test_oop_bind_returns_new_object():
    Logger.reset()
    logger = Logger.get_instance(name="oop-test")
    bound = logger.bind(request_id="req-001")
    assert bound is not logger
    assert bound._fields == {"request_id": "req-001"}


def test_oop_bind_does_not_mutate_parent():
    Logger.reset()
    logger = Logger.get_instance(name="oop-test")
    logger.bind(env="prod")
    assert not hasattr(logger, "_fields")


def test_oop_get_child_returns_logger_wrapper():
    Logger.reset()
    logger = Logger.get_instance(name="oop-test")
    child = logger.get_child("db")
    assert isinstance(child, Logger)
    assert child._name == "oop-test.db"


def test_oop_concurrent_singleton():
    import threading
    Logger.reset()
    instances = []

    def _get():
        instances.append(Logger.get_instance(name="oop-test"))

    threads = [threading.Thread(target=_get) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(set(id(i) for i in instances)) == 1


def test_oop_log_methods_do_not_raise():
    Logger.reset()
    logger = Logger.get_instance(name="oop-test", level="DEBUG")
    logger.debug("debug")
    logger.info("info")
    logger.warning("warn")
    logger.error("error")


# ── Comparison ────────────────────────────────────────────────────────────

def test_functional_bind_affects_all_subsequent_calls():
    fn_log._state.clear()
    fn_log.configure(name="cmp-fn", level="DEBUG")
    fn_log.bind(tag="shared")
    assert fn_log._state["extra"].get("tag") == "shared"


def test_oop_bind_isolated_per_adapter():
    Logger.reset()
    logger = Logger.get_instance(name="cmp-oop")
    req_log = logger.bind(tag="per-request")
    assert not hasattr(logger, "_fields")
    assert req_log._fields == {"tag": "per-request"}
