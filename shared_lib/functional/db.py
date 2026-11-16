"""
functional/db.py — Shared Library Database (Functional style)
==============================================================
Connection stored in a module-level dict keyed by name.
All operations are free functions; callers pass conn_name as a string.
Uses sqlite3 in-memory — no external DB needed to run this demo.

Key contrast with OOP:
  - No connection object to inject or close via context manager
  - Multiple DBs = multiple conn_name strings (easy to forget / mix up)
  - read-only guard must be opt-in per call site
  - Transaction is a @contextmanager, not a method
"""

import sqlite3
from contextlib import contextmanager
from typing import Any

from . import logger as log

# Module-level registry of open connections
_connections: dict[str, sqlite3.Connection] = {}


# --- lifecycle -----------------------------------------------------------

def connect(dsn: str = ":memory:", name: str = "default") -> None:
    """Open a connection and register it. Validates with SELECT 1."""
    conn = sqlite3.connect(dsn, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("SELECT 1")          # fail-fast validation
    _connections[name] = conn
    log.info(f"[DB-FN] connected: name={name!r} dsn={dsn!r}")


def disconnect(name: str = "default") -> None:
    conn = _connections.pop(name, None)
    if conn:
        conn.close()
        log.info(f"[DB-FN] disconnected: name={name!r}")


def disconnect_all() -> None:
    for name in list(_connections):
        disconnect(name)


def _get(name: str) -> sqlite3.Connection:
    if name not in _connections:
        raise RuntimeError(f"[DB-FN] no connection '{name}' — call connect() first")
    return _connections[name]


# --- queries -------------------------------------------------------------

def query(sql: str, params: tuple = (), name: str = "default") -> list[dict]:
    """SELECT — returns list of dicts."""
    rows = _get(name).execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def execute(sql: str, params: tuple = (), name: str = "default") -> int:
    """INSERT / UPDATE / DELETE — returns rows affected."""
    conn = _get(name)
    cur = conn.execute(sql, params)
    conn.commit()
    return cur.rowcount


def execute_many(sql: str, rows: list[tuple], name: str = "default") -> None:
    conn = _get(name)
    conn.executemany(sql, rows)
    conn.commit()


@contextmanager
def transaction(name: str = "default"):
    """Explicit transaction block — commits on exit, rolls back on error."""
    conn = _get(name)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def health_check(name: str = "default") -> bool:
    try:
        _get(name).execute("SELECT 1")
        return True
    except Exception:
        return False
