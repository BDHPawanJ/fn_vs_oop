"""
oop/logger.py — Shared Library Logger (OOP style)
==================================================
Logger is a class. State lives inside the instance.
Singleton via get_instance(); child loggers via get_child().

Key contrast with Functional:
  - bind() returns a NEW BoundLogger — does NOT mutate global state
  - Multiple isolated loggers possible (one per service/tenant)
  - Thread-safe singleton: double-checked lock
  - get_child() returns another Logger, not a raw stdlib object
"""

import logging
import sys
import threading
from typing import Optional

_FMT  = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_DATE = "%H:%M:%S"


class Logger:
    _instance: Optional["Logger"] = None
    _lock = threading.Lock()

    def __init__(self, name: str = "app", level: str = "DEBUG") -> None:
        self._name = name
        self._logger = self._build(name, level)

    # --- singleton -------------------------------------------------------
    @classmethod
    def get_instance(cls, name: str = "app", level: str = "DEBUG") -> "Logger":
        """Thread-safe singleton via double-checked locking."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(name, level)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton — useful in tests."""
        with cls._lock:
            cls._instance = None

    # --- construction ----------------------------------------------------
    @staticmethod
    def _build(name: str, level: str) -> logging.Logger:
        lg = logging.getLogger(name)
        lg.setLevel(getattr(logging, level.upper(), logging.DEBUG))
        if not lg.handlers:
            h = logging.StreamHandler(sys.stdout)
            h.setFormatter(logging.Formatter(_FMT, datefmt=_DATE))
            lg.addHandler(h)
        return lg

    # --- bind: returns NEW isolated logger with extra context fields -----
    def bind(self, **fields) -> "BoundLogger":
        """Return a child logger that stamps extra fields on every record."""
        return BoundLogger(self._logger, fields)

    def get_child(self, suffix: str) -> "Logger":
        """Return a Logger scoped to '<parent>.<suffix>'."""
        child = Logger.__new__(Logger)
        child._name = f"{self._name}.{suffix}"
        child._logger = self._logger.getChild(suffix)
        return child

    # --- log methods -----------------------------------------------------
    def debug(self, msg: str, **kw)     -> None: self._logger.debug(msg,     extra=kw or None)
    def info(self, msg: str, **kw)      -> None: self._logger.info(msg,      extra=kw or None)
    def warning(self, msg: str, **kw)   -> None: self._logger.warning(msg,   extra=kw or None)
    def error(self, msg: str, **kw)     -> None: self._logger.error(msg,     extra=kw or None)
    def exception(self, msg: str, **kw) -> None: self._logger.exception(msg)

    def __repr__(self) -> str:
        return f"Logger(name={self._name!r})"


class BoundLogger(Logger):
    """Logger with fixed context fields merged into every record."""

    def __init__(self, base: logging.Logger, fields: dict) -> None:
        self._name   = base.name
        self._logger = base
        self._fields = fields

    def _emit(self, level: int, msg: str, **kw) -> None:
        self._logger.log(level, msg, extra={**self._fields, **kw} or None)

    def debug(self, msg, **kw)     -> None: self._emit(logging.DEBUG,   msg, **kw)
    def info(self, msg, **kw)      -> None: self._emit(logging.INFO,    msg, **kw)
    def warning(self, msg, **kw)   -> None: self._emit(logging.WARNING, msg, **kw)
    def error(self, msg, **kw)     -> None: self._emit(logging.ERROR,   msg, **kw)
    def exception(self, msg, **kw) -> None: self._logger.exception(msg)
