"""
oop/db.py — Shared Library Database (OOP style)
================================================
DatabaseConnection owns its connection as instance state.
Context manager guarantees close(). ReadOnlyConnection adds
access control via inheritance. ConnectionPool manages multiple
connections with a queue.Queue (thread-safe acquire).

Key contrast with Functional:
  - Connection object is injectable / mockable in tests
  - Multiple DBs = multiple objects (no string key to remember)
  - ReadOnlyConnection subclass covers ALL write paths automatically
  - Pool uses queue.Queue — blocking acquire, no race condition
"""

import queue
import sqlite3
from contextlib import contextmanager
from typing import Optional

from .logger import Logger


class DatabaseConnection:
    def __init__(self, dsn: str = ":memory:", name: str = "default",
                 logger: Optional[Logger] = None) -> None:
        self._dsn    = dsn
        self._name   = name
        self._logger = logger or Logger.get_instance()
        self._conn: Optional[sqlite3.Connection] = None

    # --- lifecycle -------------------------------------------------------
    def connect(self) -> "DatabaseConnection":
        self._conn = sqlite3.connect(self._dsn, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("SELECT 1")          # validate immediately
        self._logger.info(f"[DB-OOP] connected: name={self._name!r}")
        return self

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            self._logger.info(f"[DB-OOP] closed: name={self._name!r}")

    def __enter__(self) -> "DatabaseConnection":
        return self.connect()

    def __exit__(self, *_) -> None:
        self.close()

    def _conn_or_raise(self) -> sqlite3.Connection:
        if not self._conn:
            raise RuntimeError(f"[DB-OOP] '{self._name}' not connected")
        return self._conn

    # --- queries ---------------------------------------------------------
    def query(self, sql: str, params: tuple = ()) -> list:
        rows = self._conn_or_raise().execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def execute(self, sql: str, params: tuple = ()) -> int:
        conn = self._conn_or_raise()
        cur  = conn.execute(sql, params)
        conn.commit()
        return cur.rowcount

    def execute_many(self, sql: str, rows: list) -> None:
        conn = self._conn_or_raise()
        conn.executemany(sql, rows)
        conn.commit()

    @contextmanager
    def transaction(self):
        conn = self._conn_or_raise()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def health_check(self) -> bool:
        try:
            self._conn_or_raise().execute("SELECT 1")
            return True
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"DatabaseConnection(name={self._name!r}, connected={self._conn is not None})"


# --- ReadOnlyConnection: inheritance adds access control in one place ----

class ReadOnlyConnection(DatabaseConnection):
    """Rejects any write SQL — raises PermissionError before it reaches the DB."""

    _WRITE = frozenset({"INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"})

    def _guard(self, sql: str) -> None:
        verb = sql.strip().split()[0].upper()
        if verb in self._WRITE:
            raise PermissionError(f"[DB-OOP] write denied on read-only connection: {verb}")

    def execute(self, sql: str, params: tuple = ()) -> int:
        self._guard(sql)
        return super().execute(sql, params)

    def execute_many(self, sql: str, rows: list) -> None:
        self._guard(sql)
        super().execute_many(sql, rows)


# --- ConnectionPool: thread-safe, queue.Queue backed --------------------

class ConnectionPool:
    """Lends DatabaseConnection objects from a fixed-size queue.Queue."""

    def __init__(self, dsn: str = ":memory:", size: int = 3,
                 logger: Optional[Logger] = None) -> None:
        self._dsn    = dsn
        self._size   = size
        self._logger = logger or Logger.get_instance()
        self._pool: queue.Queue = queue.Queue(maxsize=size)

    def initialise(self) -> None:
        for i in range(self._size):
            conn = DatabaseConnection(self._dsn, f"pool-{i}", self._logger).connect()
            self._pool.put_nowait(conn)
        self._logger.info(f"[POOL-OOP] ready: size={self._size}")

    @contextmanager
    def acquire(self, timeout: float = 5.0):
        """Block up to `timeout` seconds waiting for a free connection."""
        try:
            conn = self._pool.get(timeout=timeout)
        except queue.Empty:
            raise RuntimeError(f"[POOL-OOP] no connection available after {timeout}s")
        try:
            yield conn
        finally:
            self._pool.put(conn)

    def close_all(self) -> None:
        while not self._pool.empty():
            self._pool.get_nowait().close()

    def __repr__(self) -> str:
        return f"ConnectionPool(size={self._size}, available={self._pool.qsize()})"
