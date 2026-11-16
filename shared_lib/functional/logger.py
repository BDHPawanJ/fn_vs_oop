"""
functional/logger.py — Shared Library Logger (Functional style)
================================================================
State lives in a module-level dict.
Every public API is a plain function.
One global logger for the whole process.

Key contrast with OOP:
  - No class to instantiate or inject
  - Configuration stored in _state dict (implicit singleton)
  - bind() mutates global state — shared across all callers
  - Child logger = just a differently-named stdlib logger
"""

import logging
import sys
from typing import Optional

# Module-level state — the functional "singleton"
_state: dict = {}

_FMT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_DATE = "%H:%M:%S"


def configure(name: str = "app", level: str = "DEBUG") -> None:
    """Call once at startup to set up the shared logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.DEBUG))
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter(_FMT, datefmt=_DATE))
        logger.addHandler(h)
    _state["logger"] = logger
    _state["extra"] = {}


def _get() -> logging.Logger:
    if "logger" not in _state:
        configure()
    return _state["logger"]


# --- bind: attach fixed context fields to every subsequent record --------
def bind(**fields) -> None:
    """Merge fields into every log record going forward (global effect)."""
    _state.setdefault("extra", {}).update(fields)


# --- public log functions ------------------------------------------------
def debug(msg: str, **kw)    -> None: _get().debug(msg,    extra={**_state.get("extra", {}), **kw})
def info(msg: str, **kw)     -> None: _get().info(msg,     extra={**_state.get("extra", {}), **kw})
def warning(msg: str, **kw)  -> None: _get().warning(msg,  extra={**_state.get("extra", {}), **kw})
def error(msg: str, **kw)    -> None: _get().error(msg,    extra={**_state.get("extra", {}), **kw})
def exception(msg: str, **kw)-> None: _get().exception(msg)


def get_child(suffix: str) -> logging.Logger:
    """Return a child stdlib logger (name = parent.suffix)."""
    return _get().getChild(suffix)
